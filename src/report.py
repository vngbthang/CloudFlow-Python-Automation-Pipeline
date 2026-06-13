from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import get_engine
from logger import get_logger

OUTPUT_DIR = Path("data/output")
logger = get_logger(__name__)


def export_query_to_csv(query: str, output_file: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    with engine.begin() as connection:
        df = pd.read_sql_query(text(query), connection)

    output_path = OUTPUT_DIR / output_file
    df.to_csv(output_path, index=False)

    logger.info("Generated report: %s", output_path)


def generate_reports():
    daily_revenue_query = """
    SELECT
        order_date,
        SUM(revenue) AS total_revenue,
        COUNT(*) AS total_orders
    FROM orders_cleaned
    GROUP BY order_date
    ORDER BY order_date;
    """

    revenue_by_category_query = """
    SELECT
        category,
        SUM(revenue) AS total_revenue,
        COUNT(*) AS total_orders
    FROM orders_cleaned
    GROUP BY category
    ORDER BY total_revenue DESC;
    """

    order_status_summary_query = """
    SELECT
        order_status,
        COUNT(*) AS total_orders,
        SUM(revenue) AS total_revenue
    FROM orders_cleaned
    GROUP BY order_status
    ORDER BY total_orders DESC;
    """

    top_products_query = """
    SELECT
        product_name,
        SUM(revenue) AS total_revenue,
        SUM(quantity) AS total_quantity
    FROM orders_cleaned
    GROUP BY product_name
    ORDER BY total_revenue DESC;
    """

    city_revenue_query = """
    SELECT
        city,
        SUM(revenue) AS total_revenue,
        COUNT(*) AS total_orders
    FROM orders_cleaned
    GROUP BY city
    ORDER BY total_revenue DESC;
    """

    pipeline_summary_query = """
    SELECT
        (SELECT COUNT(*) FROM orders_cleaned) AS total_orders,
        (SELECT COALESCE(SUM(revenue), 0) FROM orders_cleaned) AS total_revenue,
        COUNT(*) AS total_processed_files,
        COUNT(*) FILTER (WHERE status = 'SUCCESS') AS success_files,
        COUNT(*) FILTER (WHERE status = 'FAILED') AS failed_files,
        COUNT(*) FILTER (WHERE status = 'SKIPPED_DUPLICATE') AS skipped_duplicate_files,
        CURRENT_TIMESTAMP AS generated_at
    FROM processed_files;
    """

    export_query_to_csv(daily_revenue_query, "daily_revenue.csv")
    export_query_to_csv(revenue_by_category_query, "revenue_by_category.csv")
    export_query_to_csv(order_status_summary_query, "order_status_summary.csv")
    export_query_to_csv(top_products_query, "top_products.csv")
    export_query_to_csv(city_revenue_query, "city_revenue.csv")
    export_query_to_csv(pipeline_summary_query, "pipeline_summary.csv")


if __name__ == "__main__":
    generate_reports()
