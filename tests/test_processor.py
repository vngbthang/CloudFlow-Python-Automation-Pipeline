from pathlib import Path

import pandas as pd
import pytest

from src.processor import FINAL_COLUMNS, load_and_clean_orders


def write_csv(tmp_path: Path, content: str) -> Path:
    file_path = tmp_path / "orders.csv"
    file_path.write_text(content)
    return file_path


def test_kaggle_schema_is_converted_to_unified_schema(tmp_path):
    file_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "Transaction ID,Date,Product Category,Product Name,Units Sold,Unit Price,Total Revenue,Region,Payment Method",
                "10001,2024-01-01,Electronics,iPhone 14 Pro,2,999.99,1999.98,North America,Credit Card",
            ]
        ),
    )

    df = load_and_clean_orders(file_path)

    assert df.columns.tolist() == FINAL_COLUMNS
    assert df.loc[0, "order_id"] == "10001"
    assert df.loc[0, "order_date"] == pd.Timestamp("2024-01-01").date()
    assert df.loc[0, "category"] == "Electronics"
    assert df.loc[0, "quantity"] == 2
    assert df.loc[0, "customer_id"] == "UNKNOWN"
    assert df.loc[0, "order_status"] == "Completed"
    assert df.loc[0, "city"] == "North America"


def test_old_sample_schema_is_supported(tmp_path):
    file_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "order_id,order_date,category,product_name,quantity,unit_price,order_status,customer_id,city",
                "1,2024-01-01,Books,Book A,2,10.50,completed,C001,Hanoi",
            ]
        ),
    )

    df = load_and_clean_orders(file_path)

    assert df.columns.tolist() == FINAL_COLUMNS
    assert df.loc[0, "order_status"] == "Completed"
    assert df.loc[0, "revenue"] == 21.0


def test_missing_required_columns_raise_value_error(tmp_path):
    file_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "Transaction ID,Date,Product Name,Units Sold,Unit Price,Region",
                "10001,2024-01-01,iPhone 14 Pro,2,999.99,North America",
            ]
        ),
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        load_and_clean_orders(file_path)


def test_duplicate_order_id_is_removed(tmp_path):
    file_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "order_id,order_date,category,product_name,quantity,unit_price,order_status,customer_id,city",
                "1,2024-01-01,Books,Book A,2,10.50,completed,C001,Hanoi",
                "1,2024-01-01,Books,Book A,2,10.50,completed,C001,Hanoi",
            ]
        ),
    )

    df = load_and_clean_orders(file_path)

    assert len(df) == 1
    assert df["order_id"].tolist() == ["1"]


def test_revenue_is_calculated_correctly(tmp_path):
    file_path = write_csv(
        tmp_path,
        "\n".join(
            [
                "order_id,order_date,category,product_name,quantity,unit_price,order_status,customer_id,city",
                "1,2024-01-01,Books,Book A,3,12.50,completed,C001,Hanoi",
            ]
        ),
    )

    df = load_and_clean_orders(file_path)

    assert df.loc[0, "revenue"] == 37.5
