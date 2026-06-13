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
    print(f"Current row count: {count_orders()}")
