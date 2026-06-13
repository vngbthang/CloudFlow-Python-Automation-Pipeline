# CloudFlow: Python Automation Pipeline

CloudFlow is a Python automation pipeline for processing recurring CSV business reports using AWS-compatible local services, PostgreSQL, and PowerBI-ready KPI outputs.

## Features

- Ingest CSV business reports with a Python uploader
- Store raw reports in S3-compatible storage using Floci
- Send processing jobs through an SQS-compatible queue
- Process messages with a Python worker
- Validate and clean order data using Pandas
- Store cleaned data in PostgreSQL
- Generate PowerBI-ready KPI reports using SQL

## Tech Stack

Python, SQL, Pandas, boto3, Floci, Docker, PostgreSQL, PowerBI

## Architecture

```text
CSV Reports
   ↓
Python Uploader
   ↓
Floci S3-compatible Bucket
   ↓
Floci SQS-compatible Queue
   ↓
Python Worker
   ↓
Pandas Validation and Cleaning
   ↓
PostgreSQL
   ↓
SQL KPI Reports
   ↓
PowerBI-ready CSV Outputs