import json
from pathlib import Path

import boto3

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_ENDPOINT_URL,
    AWS_REGION,
    SQS_QUEUE_NAME,
)
from processor import load_and_clean_orders
from database import create_orders_table, insert_orders, count_orders
from report import generate_reports


DOWNLOAD_DIR = Path("data/downloaded")


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

    print(f"Downloaded file from S3: s3://{bucket}/{key} -> {local_path}")
    return local_path


def process_message(s3_client, message):
    body = json.loads(message["Body"])

    bucket = body["bucket"]
    key = body["key"]

    local_file = download_file_from_s3(s3_client, bucket, key)

    cleaned_df = load_and_clean_orders(local_file)
    print(f"Cleaned rows: {len(cleaned_df)}")

    create_orders_table()
    insert_orders(cleaned_df)

    total_rows = count_orders()
    print(f"Total rows in PostgreSQL: {total_rows}")

    generate_reports()


def main():
    print("Starting CloudFlow worker...")

    s3_client = create_s3_client()
    sqs_client = create_sqs_client()
    queue_url = get_queue_url(sqs_client)

    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=5,
    )

    messages = response.get("Messages", [])

    if not messages:
        print("No messages found in queue.")
        return

    for message in messages:
        process_message(s3_client, message)

        sqs_client.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )

        print("Message processed and deleted from SQS.")

    print("CloudFlow worker completed.")


if __name__ == "__main__":
    main()
