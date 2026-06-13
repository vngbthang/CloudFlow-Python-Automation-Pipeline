import argparse
from pathlib import Path

import report
from create_resources import main as create_resources
from logger import get_logger
from upload_file import (
    create_s3_client,
    create_sqs_client,
    get_queue_url,
    send_processing_message,
    upload_file_to_s3,
)
from worker import main as run_worker

DEFAULT_INPUT_DIR = Path("data/input")
DEFAULT_OUTPUT_DIR = Path("data/output")
logger = get_logger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the CloudFlow CSV automation pipeline.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help="Directory containing CSV files to upload. Default: data/input",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for generated report CSV files. Default: data/output",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="Process one specific CSV file instead of every CSV in --input-dir.",
    )
    parser.add_argument(
        "--max-worker-runs",
        type=int,
        help="Maximum number of SQS messages for the worker to process.",
    )
    return parser.parse_args(argv)


def find_input_csv_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")

    return sorted(input_dir.glob("*.csv"))


def resolve_csv_files(input_dir: Path, file_path: Path | None) -> list[Path]:
    if file_path:
        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        if file_path.suffix.lower() != ".csv":
            raise ValueError(f"Input file must be a CSV: {file_path}")
        return [file_path]

    return find_input_csv_files(input_dir)


def upload_csv_files(csv_files: list[Path], input_dir: Path):
    if not csv_files:
        logger.info("No CSV files found in %s.", input_dir)
        return

    s3_client = create_s3_client()
    sqs_client = create_sqs_client()
    queue_url = get_queue_url(sqs_client)

    for index, csv_file in enumerate(csv_files, start=1):
        logger.info("Uploading %s/%s: %s", index, len(csv_files), csv_file)
        object_key = upload_file_to_s3(s3_client, csv_file)
        send_processing_message(sqs_client, queue_url, object_key)


def main(argv: list[str] | None = None):
    args = parse_args(argv)
    report.OUTPUT_DIR = args.output_dir

    logger.info("Running CloudFlow batch pipeline...")
    create_resources()

    csv_files = resolve_csv_files(args.input_dir, args.file)
    logger.info("CSV files found: %s", len(csv_files))

    upload_csv_files(csv_files, args.input_dir)

    if csv_files:
        logger.info("Starting worker to process queued messages...")
        max_worker_runs = args.max_worker_runs
        if max_worker_runs is None:
            max_worker_runs = len(csv_files)
        run_worker(max_messages=max_worker_runs)

    logger.info("Final report output location: %s", args.output_dir)
    logger.info("CloudFlow batch pipeline completed.")


if __name__ == "__main__":
    main()
