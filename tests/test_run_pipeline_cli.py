import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from run_pipeline import DEFAULT_INPUT_DIR, DEFAULT_OUTPUT_DIR, parse_args, resolve_csv_files


def test_parse_args_uses_default_paths():
    args = parse_args([])

    assert args.input_dir == DEFAULT_INPUT_DIR
    assert args.output_dir == DEFAULT_OUTPUT_DIR
    assert args.file is None
    assert args.max_worker_runs is None


def test_parse_args_accepts_single_file_and_worker_limit():
    args = parse_args(
        [
            "--input-dir",
            "custom/input",
            "--output-dir",
            "custom/output",
            "--file",
            "custom/input/orders.csv",
            "--max-worker-runs",
            "1",
        ]
    )

    assert args.input_dir == Path("custom/input")
    assert args.output_dir == Path("custom/output")
    assert args.file == Path("custom/input/orders.csv")
    assert args.max_worker_runs == 1


def test_resolve_csv_files_rejects_non_csv_file(tmp_path):
    text_file = tmp_path / "orders.txt"
    text_file.write_text("not,csv")

    with pytest.raises(ValueError, match="Input file must be a CSV"):
        resolve_csv_files(tmp_path, text_file)
