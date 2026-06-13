import pandas as pd
from sqlalchemy import create_engine, text

from config import DATABASE_URL


def get_engine():
    return create_engine(DATABASE_URL)


def create_orders_table():
    engine = get_engine()

    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS orders_cleaned (
        order_id TEXT PRIMARY KEY,
        order_date DATE NOT NULL,
        category TEXT NOT NULL,
        product_name TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price NUMERIC(12, 2) NOT NULL,
        order_status TEXT NOT NULL,
        customer_id TEXT,
        city TEXT,
        revenue NUMERIC(12, 2) NOT NULL
    );
    '''

    with engine.begin() as connection:
        connection.execute(text(create_table_sql))

    print("PostgreSQL table is ready: orders_cleaned")


def create_processed_files_table():
    engine = get_engine()

    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS processed_files (
        id SERIAL PRIMARY KEY,
        file_name TEXT NOT NULL,
        s3_bucket TEXT NOT NULL,
        s3_key TEXT NOT NULL,
        file_hash TEXT NOT NULL,
        status TEXT NOT NULL,
        row_count INTEGER DEFAULT 0,
        error_message TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(file_hash)
    );
    '''

    with engine.begin() as connection:
        connection.execute(text(create_table_sql))

    print("PostgreSQL table is ready: processed_files")


def is_file_hash_processed(file_hash: str) -> bool:
    engine = get_engine()

    with engine.begin() as connection:
        result = connection.execute(
            text(
                '''
                SELECT 1
                FROM processed_files
                WHERE file_hash = :file_hash
                  AND status IN ('SUCCESS', 'SKIPPED_DUPLICATE')
                LIMIT 1;
                '''
            ),
            {"file_hash": file_hash},
        )
        return result.scalar() is not None


def log_processed_file(
    file_name,
    s3_bucket,
    s3_key,
    file_hash,
    status,
    row_count=0,
    error_message=None,
):
    engine = get_engine()

    with engine.begin() as connection:
        connection.execute(
            text(
                '''
                INSERT INTO processed_files (
                    file_name,
                    s3_bucket,
                    s3_key,
                    file_hash,
                    status,
                    row_count,
                    error_message
                )
                VALUES (
                    :file_name,
                    :s3_bucket,
                    :s3_key,
                    :file_hash,
                    :status,
                    :row_count,
                    :error_message
                )
                ON CONFLICT (file_hash) DO UPDATE SET
                    file_name = EXCLUDED.file_name,
                    s3_bucket = EXCLUDED.s3_bucket,
                    s3_key = EXCLUDED.s3_key,
                    status = EXCLUDED.status,
                    row_count = EXCLUDED.row_count,
                    error_message = EXCLUDED.error_message,
                    processed_at = CURRENT_TIMESTAMP;
                '''
            ),
            {
                "file_name": file_name,
                "s3_bucket": s3_bucket,
                "s3_key": s3_key,
                "file_hash": file_hash,
                "status": status,
                "row_count": row_count,
                "error_message": error_message,
            },
        )

    print(f"Logged processed file: {file_name} ({status})")


def insert_orders(df: pd.DataFrame):
    engine = get_engine()

    with engine.begin() as connection:
        for _, row in df.iterrows():
            connection.execute(
                text(
                    '''
                    INSERT INTO orders_cleaned (
                        order_id,
                        order_date,
                        category,
                        product_name,
                        quantity,
                        unit_price,
                        order_status,
                        customer_id,
                        city,
                        revenue
                    )
                    VALUES (
                        :order_id,
                        :order_date,
                        :category,
                        :product_name,
                        :quantity,
                        :unit_price,
                        :order_status,
                        :customer_id,
                        :city,
                        :revenue
                    )
                    ON CONFLICT (order_id) DO UPDATE SET
                        order_date = EXCLUDED.order_date,
                        category = EXCLUDED.category,
                        product_name = EXCLUDED.product_name,
                        quantity = EXCLUDED.quantity,
                        unit_price = EXCLUDED.unit_price,
                        order_status = EXCLUDED.order_status,
                        customer_id = EXCLUDED.customer_id,
                        city = EXCLUDED.city,
                        revenue = EXCLUDED.revenue;
                    '''
                ),
                {
                    "order_id": row["order_id"],
                    "order_date": row["order_date"],
                    "category": row["category"],
                    "product_name": row["product_name"],
                    "quantity": int(row["quantity"]),
                    "unit_price": float(row["unit_price"]),
                    "order_status": row["order_status"],
                    "customer_id": row["customer_id"],
                    "city": row["city"],
                    "revenue": float(row["revenue"]),
                },
            )

    print(f"Inserted/updated {len(df)} rows into PostgreSQL.")


def count_orders():
    engine = get_engine()

    with engine.begin() as connection:
        result = connection.execute(text("SELECT COUNT(*) FROM orders_cleaned;"))
        return result.scalar()


if __name__ == "__main__":
    create_orders_table()
    create_processed_files_table()
    print(f"Current row count: {count_orders()}")
