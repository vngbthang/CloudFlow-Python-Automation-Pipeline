from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "category",
    "product_name",
    "quantity",
    "unit_price",
    "order_status",
    "customer_id",
    "city",
]

FINAL_COLUMNS = REQUIRED_COLUMNS + ["revenue"]

KAGGLE_COLUMN_MAP = {
    "Transaction ID": "order_id",
    "Date": "order_date",
    "Product Category": "category",
    "Product Name": "product_name",
    "Units Sold": "quantity",
    "Unit Price": "unit_price",
    "Region": "city",
}


def _generate_order_status(row_number: int) -> str:
    if row_number % 20 == 0:
        return "Cancelled"
    if row_number % 7 == 0:
        return "Pending"
    return "Completed"


def _standardize_schema(df: pd.DataFrame) -> pd.DataFrame:
    if all(col in df.columns for col in REQUIRED_COLUMNS):
        return df[REQUIRED_COLUMNS].copy()

    kaggle_columns = list(KAGGLE_COLUMN_MAP)
    missing_kaggle_columns = [col for col in kaggle_columns if col not in df.columns]
    if missing_kaggle_columns:
        missing_sample_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        raise ValueError(
            "Missing required columns. "
            f"Sample schema missing: {missing_sample_columns}. "
            f"Kaggle schema missing: {missing_kaggle_columns}."
        )

    standardized = df[kaggle_columns].rename(columns=KAGGLE_COLUMN_MAP).copy()
    standardized["customer_id"] = "UNKNOWN"
    standardized["order_status"] = [
        _generate_order_status(row_number) for row_number in range(1, len(standardized) + 1)
    ]

    return standardized[REQUIRED_COLUMNS]


def load_and_clean_orders(file_path: str | Path) -> pd.DataFrame:
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    df = pd.read_csv(file_path)
    df = _standardize_schema(df)

    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["order_status"] = df["order_status"].astype(str).str.strip().str.title()
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip()

    string_columns = [
        "order_id",
        "category",
        "product_name",
        "order_status",
        "customer_id",
        "city",
    ]
    df[string_columns] = df[string_columns].replace(
        {"": pd.NA, "nan": pd.NA, "Nan": pd.NA, "None": pd.NA}
    )

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce").dt.date
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")

    df = df.dropna(
        subset=[
            "order_id",
            "order_date",
            "category",
            "product_name",
            "quantity",
            "unit_price",
            "order_status",
        ]
    )

    df = df[df["quantity"] > 0]
    df = df[df["unit_price"] >= 0]

    df["revenue"] = df["quantity"] * df["unit_price"]

    df = df.drop_duplicates(subset=["order_id"])

    return df[FINAL_COLUMNS]


if __name__ == "__main__":
    cleaned_df = load_and_clean_orders("data/input/orders_kaggle.csv")
    print(cleaned_df)
