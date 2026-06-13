from pathlib import Path

import pandas as pd

OUTPUT_DIR = Path("data/output")
POWERBI_DATASET = OUTPUT_DIR / "powerbi_dashboard_dataset.csv"

REPORT_SPECS = {
    "daily_revenue.csv": {
        "report_type": "daily_revenue",
        "dimension_column": "order_date",
        "metrics": ["total_revenue", "total_orders"],
    },
    "revenue_by_category.csv": {
        "report_type": "revenue_by_category",
        "dimension_column": "category",
        "metrics": ["total_revenue", "total_orders"],
    },
    "order_status_summary.csv": {
        "report_type": "order_status_summary",
        "dimension_column": "order_status",
        "metrics": ["total_orders", "total_revenue"],
    },
    "top_products.csv": {
        "report_type": "top_products",
        "dimension_column": "product_name",
        "metrics": ["total_revenue", "total_quantity"],
    },
    "city_revenue.csv": {
        "report_type": "city_revenue",
        "dimension_column": "city",
        "metrics": ["total_revenue", "total_orders"],
    },
}


def validate_columns(df: pd.DataFrame, report_file: str, required_columns: list[str]) -> None:
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(f"{report_file} is missing required columns: {missing_columns}")


def convert_dimension_report(report_file: str, spec: dict[str, object]) -> list[dict[str, object]]:
    report_path = OUTPUT_DIR / report_file
    if not report_path.exists():
        raise FileNotFoundError(f"Missing report file: {report_path}")

    df = pd.read_csv(report_path)
    dimension_column = str(spec["dimension_column"])
    metrics = list(spec["metrics"])
    validate_columns(df, report_file, [dimension_column, *metrics])

    rows = []
    for _, record in df.iterrows():
        for metric in metrics:
            rows.append(
                {
                    "report_type": spec["report_type"],
                    "dimension": record[dimension_column],
                    "metric": metric,
                    "value": record[metric],
                }
            )
    return rows


def convert_pipeline_summary() -> list[dict[str, object]]:
    report_file = "pipeline_summary.csv"
    report_path = OUTPUT_DIR / report_file
    if not report_path.exists():
        raise FileNotFoundError(f"Missing report file: {report_path}")

    df = pd.read_csv(report_path)
    if df.empty:
        return []

    numeric_df = df.apply(pd.to_numeric, errors="coerce")
    numeric_columns = [column for column in df.columns if numeric_df[column].notna().any()]

    rows = []
    first_row = df.iloc[0]
    for metric in numeric_columns:
        rows.append(
            {
                "report_type": "pipeline_summary",
                "dimension": "summary",
                "metric": metric,
                "value": first_row[metric],
            }
        )
    return rows


def create_powerbi_dataset() -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for report_file, spec in REPORT_SPECS.items():
        rows.extend(convert_dimension_report(report_file, spec))

    rows.extend(convert_pipeline_summary())

    dataset = pd.DataFrame(rows, columns=["report_type", "dimension", "metric", "value"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(POWERBI_DATASET, index=False)
    return dataset


def main() -> None:
    dataset = create_powerbi_dataset()
    print(f"Created PowerBI single CSV: {POWERBI_DATASET}")
    print(f"Rows written: {len(dataset)}")


if __name__ == "__main__":
    main()
