import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import boto3

from config import (
    AWS_ACCESS_KEY_ID,
    AWS_ENDPOINT_URL,
    AWS_REGION,
    AWS_SECRET_ACCESS_KEY,
    S3_BUCKET,
    SQS_QUEUE_NAME,
)
from logger import get_logger

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


def upload_file_to_s3(s3_client, file_path: Path):
    object_key = file_path.name
    s3_client.upload_file(str(file_path), S3_BUCKET, object_key)
    logger.info("Uploaded file to S3: s3://%s/%s", S3_BUCKET, object_key)
    return object_key


def send_processing_message(sqs_client, queue_url: str, object_key: str):
    message = {
        "bucket": S3_BUCKET,
        "key": object_key,
        "uploaded_at": datetime.now(UTC).isoformat(),
    }

    response = sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message),
    )

    logger.info("Sent processing message to SQS. MessageId: %s", response["MessageId"])


def main():
    if len(sys.argv) < 2:
        logger.error("Usage: python src/upload_file.py <csv_file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1])

    if not file_path.exists():
        logger.error("File not found: %s", file_path)
        sys.exit(1)

    if file_path.suffix.lower() != ".csv":
        logger.error("Only CSV files are supported.")
        sys.exit(1)

    s3_client = create_s3_client()
    sqs_client = create_sqs_client()

    queue_url = get_queue_url(sqs_client)
    object_key = upload_file_to_s3(s3_client, file_path)
    send_processing_message(sqs_client, queue_url, object_key)

    logger.info("Upload workflow completed.")


if __name__ == "__main__":
    main()
