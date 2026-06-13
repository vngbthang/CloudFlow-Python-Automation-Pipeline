import json
from pathlib import Path

import boto3

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_ENDPOINT_URL,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    SQS_QUEUE_NAME,
)
from database import (
    count_orders,
    create_orders_table,
    create_processed_files_table,
    insert_orders,
    is_file_hash_processed,
    log_processed_file,
)
from logger import get_logger
from processor import load_and_clean_orders
from report import generate_reports
from utils import calculate_file_hash

DOWNLOAD_DIR = Path("data/downloaded")
logger = get_logger(__name__)


def create_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def create_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def get_queue_url(sqs_client):
    response = sqs_client.get_queue_url(QueueName=SQS_QUEUE_NAME)
    return response["QueueUrl"]


def download_file_from_s3(s3_client, bucket: str, key: str) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    local_path = DOWNLOAD_DIR / key
    s3_client.download_file(bucket, key, str(local_path))

    logger.info("Downloaded file from S3: s3://%s/%s -> %s", bucket, key, local_path)
    return local_path


def process_message(s3_client, message):
    body = json.loads(message["Body"])

    bucket = body["bucket"]
    key = body["key"]
    file_name = Path(key).name

    local_file = download_file_from_s3(s3_client, bucket, key)
    file_hash = calculate_file_hash(local_file)
    logger.info("File SHA256: %s", file_hash)

    if is_file_hash_processed(file_hash):
        logger.warning("Skipping duplicate file: %s", file_name)
        log_processed_file(
            file_name=file_name,
            s3_bucket=bucket,
            s3_key=key,
            file_hash=file_hash,
            status="SKIPPED_DUPLICATE",
            row_count=0,
            error_message="Duplicate file hash already processed successfully.",
        )
        generate_reports()
        return

    cleaned_df = load_and_clean_orders(local_file)
    logger.info("Cleaned rows: %s", len(cleaned_df))

    insert_orders(cleaned_df)

    total_rows = count_orders()
    logger.info("Total rows in PostgreSQL: %s", total_rows)

    generate_reports()
    log_processed_file(
        file_name=file_name,
        s3_bucket=bucket,
        s3_key=key,
        file_hash=file_hash,
        status="SUCCESS",
        row_count=len(cleaned_df),
    )


def main(max_messages: int | None = None):
    logger.info("Starting CloudFlow worker...")

    s3_client = create_s3_client()
    sqs_client = create_sqs_client()
    queue_url = get_queue_url(sqs_client)
    processed_messages = 0

    create_orders_table()
    create_processed_files_table()

    while max_messages is None or processed_messages < max_messages:
        response = sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=5,
        )

        messages = response.get("Messages", [])

        if not messages:
            logger.info("No messages found in queue.")
            break

        for message in messages:
            try:
                process_message(s3_client, message)
            except Exception as exc:
                error_message = str(exc)
                logger.error("Failed to process message: %s", error_message)

                try:
                    body = json.loads(message["Body"])
                    bucket = body.get("bucket", "")
                    key = body.get("key", "")
                    file_name = Path(key).name if key else "UNKNOWN"
                    local_file = DOWNLOAD_DIR / key if key else None
                    file_hash = (
                        calculate_file_hash(local_file)
                        if local_file and local_file.exists()
                        else f"FAILED-{message.get('MessageId', 'UNKNOWN')}"
                    )
                    log_processed_file(
                        file_name=file_name,
                        s3_bucket=bucket,
                        s3_key=key,
                        file_hash=file_hash,
                        status="FAILED",
                        row_count=0,
                        error_message=error_message,
                    )
                    generate_reports()
                except Exception as log_exc:
                    logger.error("Failed to log processing failure: %s", log_exc)
                    raise

            sqs_client.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message["ReceiptHandle"],
            )
            processed_messages += 1
            logger.info(
                "Message processed and deleted from SQS. Count: %s",
                processed_messages,
            )

    logger.info("CloudFlow worker completed.")


if __name__ == "__main__":
    main()
