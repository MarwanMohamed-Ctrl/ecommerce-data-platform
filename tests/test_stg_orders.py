import os
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def get_connection():
    required = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]

    if missing:
        pytest.fail(f"Missing database settings: {', '.join(missing)}")

    return psycopg.connect(
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        connect_timeout=5,
    )


def test_stg_orders_has_expected_columns():
    with get_connection() as conn:
        columns = {
            row[0]
            for row in conn.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'staging'
                  AND table_name = 'stg_orders'
                """
            )
        }

    expected = {
        "order_id",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "is_approval_before_purchase",
        "is_carrier_before_approval",
        "is_customer_delivery_before_carrier",
    }

    assert expected.issubset(columns), (
        f"Missing staging columns: {sorted(expected - columns)}"
    )


def test_stg_orders_row_count():
    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM staging.stg_orders"
        ).fetchone()[0]

    assert count == 99_441


def test_stg_orders_quality_flags():
    with get_connection() as conn:
        result = conn.execute(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE is_approval_before_purchase IS TRUE
                ),
                COUNT(*) FILTER (
                    WHERE is_carrier_before_approval IS TRUE
                ),
                COUNT(*) FILTER (
                    WHERE is_customer_delivery_before_carrier IS TRUE
                )
            FROM staging.stg_orders
            """
        ).fetchone()

    assert result == (0, 1359, 23)
