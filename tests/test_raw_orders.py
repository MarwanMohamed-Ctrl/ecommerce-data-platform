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


def test_raw_orders_have_no_missing_order_ids():
    with get_connection() as conn:
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM raw_olist.olist_orders
            WHERE NULLIF(order_id, '') IS NULL
            """
        ).fetchone()[0]

    assert count == 0, f"Found {count} raw orders without an order ID"


def test_raw_orders_have_unique_order_ids():
    with get_connection() as conn:
        duplicates = conn.execute(
            """
            SELECT COUNT(*) - COUNT(DISTINCT NULLIF(order_id, ''))
            FROM raw_olist.olist_orders
            """
        ).fetchone()[0]

    assert duplicates == 0, f"Found {duplicates} missing or duplicate order IDs"
