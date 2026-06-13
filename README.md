# CloudFlow: Python Automation Pipeline

CloudFlow is a local production-like Python automation pipeline for recurring CSV business reports. It uses Kaggle online sales CSV data, Floci to emulate AWS-compatible S3/SQS locally, PostgreSQL for cleaned data and processing logs, and SQL-generated PowerBI-ready KPI reports.

The pipeline tracks processed files with SHA256 hashes, prevents duplicate processing, and logs failed files without crashing the whole worker.

## Tech Stack

Python, SQL, Pandas, boto3, Floci, Docker, PostgreSQL, PowerBI, pytest

## Architecture

```text
Kaggle CSV Reports
   ↓
Python Batch Runner
   ↓
Floci S3-compatible Bucket
   ↓
Floci SQS-compatible Queue
   ↓
Python Worker
   ↓
File Hash + Duplicate Check
   ↓
Pandas Validation and Cleaning
   ↓
PostgreSQL orders_cleaned + processed_files
   ↓
SQL KPI Reports
   ↓
PowerBI-ready CSV Outputs
```

## What It Does

- Uploads every CSV file in `data/input/` to a Floci S3-compatible bucket
- Sends one SQS-compatible processing message per uploaded file
- Downloads each queued file in the worker
- Calculates a SHA256 file hash and checks `processed_files`
- Skips duplicate files that were already processed
- Validates and cleans order data with Pandas
- Inserts cleaned rows into PostgreSQL `orders_cleaned`
- Logs SUCCESS, FAILED, and SKIPPED_DUPLICATE file outcomes in `processed_files`
- Generates PowerBI-ready CSV reports in `data/output/`

## Input Data

The main input is the Kaggle online sales dataset:

```text
data/input/orders_kaggle.csv
```

The processor supports both the Kaggle schema and the original sample order schema. The file `data/input/orders_bad.csv` is intentionally invalid so the pipeline can demonstrate FAILED file tracking.

## Setup and Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker compose up -d
python src\run_pipeline.py
pytest
```

## Generated Reports

Reports are written to `data/output/`:

- `daily_revenue.csv`
- `revenue_by_category.csv`
- `order_status_summary.csv`
- `top_products.csv`
- `city_revenue.csv`
- `pipeline_summary.csv`

## Verify PostgreSQL Tracking

Open a PostgreSQL shell:

```powershell
docker exec -it cloudflow-postgres psql -U cloudflow -d cloudflow_db
```

Check processing history:

```sql
SELECT file_name, status, row_count, error_message, processed_at
FROM processed_files
ORDER BY processed_at DESC;
```

Run the pipeline twice to verify duplicate skipping. The second run should mark already-seen file hashes as `SKIPPED_DUPLICATE` and should not insert duplicate orders.

Check failed file tracking:

```sql
SELECT file_name, status, error_message
FROM processed_files
WHERE status = 'FAILED';
```

`orders_bad.csv` should appear as a failed file because it is intentionally missing required columns.
