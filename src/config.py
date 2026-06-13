import os
from dotenv import load_dotenv

load_dotenv()

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")

S3_BUCKET = os.getenv("S3_BUCKET", "cloudflow-raw-reports")
SQS_QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "cloudflow-processing-queue")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5433")
POSTGRES_DB = os.getenv("POSTGRES_DB", "cloudflow_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "cloudflow")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "cloudflow")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
