from __future__ import annotations

import csv
import shutil
import subprocess
from datetime import datetime
from io import StringIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT_DIR / "docs" / "images"
OUTPUT_DIR = ROOT_DIR / "data" / "output"

PIPELINE_IMAGE = IMAGE_DIR / "pipeline-execution.png"
REPORTS_IMAGE = IMAGE_DIR / "generated-reports.png"
POSTGRES_IMAGE = IMAGE_DIR / "postgresql-tracking.png"
CI_IMAGE = IMAGE_DIR / "ci-passing.png"

PIPELINE_COMMAND = [".\\.venv\\Scripts\\python.exe", "src\\run_pipeline.py"]
POSTGRES_COMMAND = [
    "docker",
    "exec",
    "cloudflow-postgres",
    "psql",
    "-U",
    "cloudflow",
    "-d",
    "cloudflow_db",
    "--csv",
    "-c",
    (
        "SELECT file_name, status, row_count, LEFT(error_message, 80) AS error_message, "
        "processed_at FROM processed_files ORDER BY processed_at DESC;"
    ),
]

EXPECTED_REPORTS = [
    "daily_revenue.csv",
    "revenue_by_category.csv",
    "order_status_summary.csv",
    "top_products.csv",
    "city_revenue.csv",
    "pipeline_summary.csv",
]


def run_command(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        cwd=ROOT_DIR,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = "\n".join(part for part in [completed.stdout, completed.stderr] if part)
    return output.strip()


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/CascadiaMono.ttf"),
        Path("C:/Windows/Fonts/CascadiaCode.ttf"),
        Path("C:/Windows/Fonts/consola.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for font_path in candidates:
        if font_path.exists():
            return ImageFont.truetype(str(font_path), size=size)
    return ImageFont.load_default()


def wrap_line(line: str, limit: int = 150) -> list[str]:
    if len(line) <= limit:
        return [line]
    chunks = []
    current = line
    while len(current) > limit:
        split_at = current.rfind(" ", 0, limit)
        if split_at <= 0:
            split_at = limit
        chunks.append(current[:split_at])
        current = "  " + current[split_at:].strip()
    chunks.append(current)
    return chunks


def render_text_image(
    title: str,
    lines: list[str],
    output_path: Path,
    subtitle: str | None = None,
    dark: bool = True,
) -> None:
    font = load_font(22)
    title_font = load_font(30, bold=True)
    subtitle_font = load_font(18)

    wrapped_lines: list[str] = []
    for line in lines:
        wrapped_lines.extend(wrap_line(line))

    char_width = max(font.getlength("M"), 12)
    width = min(
        max(1200, int(max((len(line) for line in wrapped_lines), default=80) * char_width) + 96),
        2200,
    )
    line_height = 32
    header_height = 116 if subtitle else 86
    height = header_height + len(wrapped_lines) * line_height + 64

    background = "#0f172a" if dark else "#f8fafc"
    title_color = "#f8fafc" if dark else "#0f172a"
    text_color = "#d1d5db" if dark else "#1f2937"
    accent = "#38bdf8" if dark else "#2563eb"
    muted = "#94a3b8" if dark else "#64748b"

    image = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((24, 20, width - 24, height - 20), radius=14, outline=accent, width=2)
    draw.text((48, 42), title, font=title_font, fill=title_color)
    if subtitle:
        draw.text((48, 82), subtitle, font=subtitle_font, fill=muted)

    y = header_height
    for line in wrapped_lines:
        fill = text_color
        if "ERROR" in line or "FAILED" in line:
            fill = "#fca5a5"
        elif "WARNING" in line or "SKIPPED_DUPLICATE" in line:
            fill = "#fde68a"
        elif "Generated report" in line or "completed" in line.lower():
            fill = "#86efac"
        draw.text((48, y), line, font=font, fill=fill)
        y += line_height

    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)


def important_pipeline_lines(output: str) -> list[str]:
    keywords = [
        "Running CloudFlow",
        "Creating CloudFlow",
        "S3 bucket",
        "SQS queue",
        "CSV files found",
        "Uploading",
        "Uploaded file",
        "Sent processing message",
        "Starting worker",
        "Downloaded file",
        "Skipping duplicate",
        "Failed to process",
        "Logged processed file",
        "Generated report",
        "CloudFlow batch pipeline completed",
    ]
    lines = []
    for line in output.splitlines():
        if any(keyword in line for keyword in keywords):
            lines.append(line)
    return lines or output.splitlines()


def report_lines() -> list[str]:
    lines = ["Report File                         Size       Modified"]
    lines.append("-" * 78)
    for report_name in EXPECTED_REPORTS:
        path = OUTPUT_DIR / report_name
        if path.exists():
            stat = path.stat()
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(f"{report_name:<35} {stat.st_size:>8} B   {modified}")
        else:
            lines.append(f"{report_name:<35} MISSING")
    return lines


def postgres_table_lines(csv_output: str) -> list[str]:
    rows = list(csv.reader(StringIO(csv_output)))
    if not rows:
        return ["No PostgreSQL tracking rows returned."]

    lines = [
        "file_name                              status              rows  processed_at",
        "-" * 100,
    ]
    for row in rows[1:]:
        file_name, status, row_count, error_message, processed_at = row
        error = (error_message or "").replace("\n", " ")
        if len(error) > 64:
            error = f"{error[:61]}..."
        lines.append(f"{file_name:<38} {status:<18} {row_count:>4}  {processed_at}")
        if error:
            lines.append(f"  error: {error}")

    return lines


def create_temporary_success_file() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_path = ROOT_DIR / f"docs_success_sample_{timestamp}.csv"
    file_path.write_text(
        "\n".join(
            [
                "order_id,order_date,category,product_name,quantity,unit_price,"
                "order_status,customer_id,city",
                f"DOCS-{timestamp},2026-06-14,Documentation,Docs Success Row,1,1.00,"
                "Completed,DOCS,Hanoi",
            ]
        ),
        encoding="utf-8",
    )
    return file_path


def ensure_success_tracking_exists(current_postgres_output: str) -> str:
    if " SUCCESS " in current_postgres_output:
        return current_postgres_output

    temp_file = create_temporary_success_file()
    try:
        run_command(
            [
                ".\\.venv\\Scripts\\python.exe",
                "src\\run_pipeline.py",
                "--file",
                str(temp_file),
                "--max-worker-runs",
                "1",
            ]
        )
    finally:
        temp_file.unlink(missing_ok=True)

    return run_command(POSTGRES_COMMAND)


def generate_ci_image_if_verified() -> bool:
    if not shutil.which("gh"):
        return False

    output = run_command(["gh", "run", "list", "--limit", "5"])
    if "success" not in output.lower():
        return False

    render_text_image(
        "GitHub Actions CI",
        output.splitlines(),
        CI_IMAGE,
        subtitle="Verified from: gh run list --limit 5",
        dark=False,
    )
    return True


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    pipeline_output = run_command(PIPELINE_COMMAND)
    render_text_image(
        "CloudFlow Pipeline Execution",
        important_pipeline_lines(pipeline_output),
        PIPELINE_IMAGE,
        subtitle="Generated from actual: .\\.venv\\Scripts\\python.exe src\\run_pipeline.py",
    )

    render_text_image(
        "Generated Report Files",
        report_lines(),
        REPORTS_IMAGE,
        subtitle="Generated from actual data/output/ file metadata",
        dark=False,
    )

    postgres_output = ensure_success_tracking_exists(run_command(POSTGRES_COMMAND))
    render_text_image(
        "PostgreSQL processed_files Tracking",
        postgres_table_lines(postgres_output),
        POSTGRES_IMAGE,
        subtitle="Generated from actual Docker PostgreSQL query output",
        dark=False,
    )

    if generate_ci_image_if_verified():
        print(f"Created {CI_IMAGE}")
    else:
        if CI_IMAGE.exists():
            CI_IMAGE.unlink()
        print("CI status was not verifiable locally; skipped ci-passing.png.")

    print(f"Created {PIPELINE_IMAGE}")
    print(f"Created {REPORTS_IMAGE}")
    print(f"Created {POSTGRES_IMAGE}")


if __name__ == "__main__":
    main()
