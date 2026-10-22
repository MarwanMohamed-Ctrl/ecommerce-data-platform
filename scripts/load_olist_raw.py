import csv
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "olist"

# Explicit mappings prevent accidental loading into the wrong table.
TABLES = {
    "olist_customers_dataset.csv": (
        "olist_customers",
        (
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ),
    ),
    "olist_geolocation_dataset.csv": (
        "olist_geolocation",
        (
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ),
    ),
    "olist_order_items_dataset.csv": (
        "olist_order_items",
        (
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ),
    ),
    "olist_order_payments_dataset.csv": (
        "olist_order_payments",
        (
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ),
    ),
    "olist_order_reviews_dataset.csv": (
        "olist_order_reviews",
        (
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ),
    ),
    "olist_orders_dataset.csv": (
        "olist_orders",
        (
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ),
    ),
    "olist_products_dataset.csv": (
        "olist_products",
        (
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ),
    ),
    "olist_sellers_dataset.csv": (
        "olist_sellers",
        (
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ),
    ),
    "product_category_name_translation.csv": (
        "product_category_translation",
        (
            "product_category_name",
            "product_category_name_english",
        ),
    ),
}


def connect_to_postgres():
    load_dotenv(PROJECT_ROOT / ".env")

    required = (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
    )
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            f"Missing required .env variables: {', '.join(missing)}"
        )

    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=5,
    )


def load_file(conn, filename, table_name, columns):
    path = DATA_DIR / filename

    if not path.is_file():
        raise FileNotFoundError(f"Source file not found: {path}")

    loaded_rows = 0
    copy_columns = ("source_file", *columns)
    column_sql = ", ".join(f'"{column}"' for column in copy_columns)
    copy_sql = (
        f"COPY raw_olist.{table_name} ({column_sql}) "
        "FROM STDIN"
    )

    # Each file is replaced atomically. If COPY fails, its transaction
    # rolls back and the previous contents of that table are retained.
    with conn.transaction():
        with path.open(
            "r", encoding="utf-8-sig", newline=""
        ) as source:
            reader = csv.DictReader(source)

            if tuple(reader.fieldnames or ()) != columns:
                raise ValueError(
                    f"Unexpected CSV headers in {filename}: "
                    f"{reader.fieldnames}"
                )

            with conn.cursor() as cur:
                cur.execute(
                    f"TRUNCATE TABLE raw_olist.{table_name} "
                    "RESTART IDENTITY"
                )

                with cur.copy(copy_sql) as copy:
                    for row in reader:
                        if None in row:
                            raise ValueError(
                                f"Extra fields in {filename}, "
                                f"CSV record {loaded_rows + 2}"
                            )

                        values = [filename]
                        values.extend(row[column] for column in columns)
                        copy.write_row(values)
                        loaded_rows += 1

    with conn.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) FROM raw_olist.{table_name}"
        )
        stored_rows = cur.fetchone()[0]

    if stored_rows != loaded_rows:
        raise RuntimeError(
            f"{filename}: read {loaded_rows} rows but found "
            f"{stored_rows} in PostgreSQL"
        )

    print(f"{filename}: {stored_rows:,} rows loaded")


def main():
    if not DATA_DIR.is_dir():
        raise SystemExit(f"Data directory not found: {DATA_DIR}")

    expected_files = set(TABLES)
    actual_files = {
        path.name for path in DATA_DIR.glob("*.csv")
    }

    missing = sorted(expected_files - actual_files)
    unexpected = sorted(actual_files - expected_files)

    if missing or unexpected:
        if missing:
            print(f"Missing CSV files: {missing}")
        if unexpected:
            print(f"Unexpected CSV files: {unexpected}")
        raise SystemExit("Source file validation failed.")

    total_rows = 0

    with connect_to_postgres() as conn:
        for filename, (table_name, columns) in TABLES.items():
            load_file(conn, filename, table_name, columns)

            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT COUNT(*) FROM raw_olist.{table_name}"
                )
                total_rows += cur.fetchone()[0]

    print(f"\nTotal raw rows loaded: {total_rows:,}")


if __name__ == "__main__":
    main()
