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


def load_and_clean_orders(file_path: str | Path) -> pd.DataFrame:
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    df = pd.read_csv(file_path)

    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df = df[REQUIRED_COLUMNS].copy()

    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["category"] = df["category"].astype(str).str.strip()
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["order_status"] = df["order_status"].astype(str).str.strip().str.title()
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["city"] = df["city"].astype(str).str.strip()

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

    return df


if __name__ == "__main__":
    cleaned_df = load_and_clean_orders("data/input/orders_sample.csv")
    print(cleaned_df)
