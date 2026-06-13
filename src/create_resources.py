import boto3
from botocore.exceptions import ClientError

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


def create_bucket_if_not_exists(s3_client):
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        logger.info("S3 bucket already exists: %s", S3_BUCKET)
    except ClientError:
        s3_client.create_bucket(Bucket=S3_BUCKET)
        logger.info("Created S3 bucket: %s", S3_BUCKET)


def create_queue_if_not_exists(sqs_client):
    response = sqs_client.create_queue(QueueName=SQS_QUEUE_NAME)
    queue_url = response["QueueUrl"]
    logger.info("SQS queue ready: %s", SQS_QUEUE_NAME)
    logger.info("Queue URL: %s", queue_url)
    return queue_url


def main():
    logger.info("Creating CloudFlow local AWS-compatible resources...")

    s3_client = create_s3_client()
    sqs_client = create_sqs_client()

    create_bucket_if_not_exists(s3_client)
    create_queue_if_not_exists(sqs_client)

    logger.info("CloudFlow resources are ready.")


if __name__ == "__main__":
    main()
