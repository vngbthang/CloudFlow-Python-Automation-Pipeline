from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import get_engine


OUTPUT_DIR = Path("data/output")


def export_query_to_csv(query: str, output_file: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    engine = get_engine()

    with engine.begin() as connection:
        df = pd.read_sql_query(text(query), connection)

    output_path = OUTPUT_DIR / output_file
    df.to_csv(output_path, index=False)

    print(f"Generated report: {output_path}")


def generate_reports():
    daily_revenue_query = '''
    SELECT
        order_date,
        SUM(revenue) AS total_revenue,
        COUNT(*) AS total_orders
    FROM orders_cleaned
    GROUP BY order_date
    ORDER BY order_date;
    '''

    revenue_by_category_query = '''
    SELECT
        category,
        SUM(revenue) AS total_revenue,
        COUNT(*) AS total_orders
    FROM orders_cleaned
    GROUP BY category
    ORDER BY total_revenue DESC;
    '''

    order_status_summary_query = '''
    SELECT
        order_status,
        COUNT(*) AS total_orders,
        SUM(revenue) AS total_revenue
    FROM orders_cleaned
    GROUP BY order_status
    ORDER BY total_orders DESC;
    '''

    export_query_to_csv(daily_revenue_query, "daily_revenue.csv")
    export_query_to_csv(revenue_by_category_query, "revenue_by_category.csv")
    export_query_to_csv(order_status_summary_query, "order_status_summary.csv")


if __name__ == "__main__":
    generate_reports()
