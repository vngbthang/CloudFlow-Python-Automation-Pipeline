from pathlib import Path

from create_resources import main as create_resources
from upload_file import (
    create_s3_client,
    create_sqs_client,
    get_queue_url,
    send_processing_message,
    upload_file_to_s3,
)
from worker import main as run_worker


INPUT_DIR = Path("data/input")


def find_input_csv_files() -> list[Path]:
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}")

    return sorted(INPUT_DIR.glob("*.csv"))


def upload_csv_files(csv_files: list[Path]):
    if not csv_files:
        print(f"No CSV files found in {INPUT_DIR}.")
        return

    s3_client = create_s3_client()
    sqs_client = create_sqs_client()
    queue_url = get_queue_url(sqs_client)

    for index, csv_file in enumerate(csv_files, start=1):
        print(f"Uploading {index}/{len(csv_files)}: {csv_file}")
        object_key = upload_file_to_s3(s3_client, csv_file)
        send_processing_message(sqs_client, queue_url, object_key)


def main():
    print("Running CloudFlow batch pipeline...")
    create_resources()

    csv_files = find_input_csv_files()
    print(f"CSV files found: {len(csv_files)}")

    upload_csv_files(csv_files)

    if csv_files:
        print("Starting worker to process queued messages...")
        run_worker()

    print("Final report output location: data/output/")
    print("CloudFlow batch pipeline completed.")


if __name__ == "__main__":
    main()
