
import os
import uuid
from datetime import datetime
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


def test_stg_orders_matches_raw_row_count():
    with get_connection() as conn:
        raw_count = conn.execute(
            "SELECT COUNT(*) FROM raw_olist.olist_orders"
        ).fetchone()[0]

        staging_count = conn.execute(
            "SELECT COUNT(*) FROM staging.stg_orders"
        ).fetchone()[0]

    assert staging_count == raw_count, (
        f"Staging has {staging_count} rows, "
        f"but raw has {raw_count} rows"
    )


def test_stg_orders_quality_flags():
    prefix = f"test-{uuid.uuid4().hex}-"
    base = datetime(2020, 1, 1, 10, 0, 0)

    orders = [
        # Valid timestamp chronology.
        (prefix + "valid", base, base.replace(hour=11),
         base.replace(hour=12), base.replace(hour=13)),
        # Approval before purchase.
        (prefix + "approval", base, base.replace(hour=9),
         base.replace(hour=12), base.replace(hour=13)),
        # Carrier timestamp before approval.
        (prefix + "carrier", base, base.replace(hour=11),
         base.replace(hour=10), base.replace(hour=13)),
        # Customer delivery before carrier timestamp.
        (prefix + "delivery", base, base.replace(hour=11),
         base.replace(hour=12), base.replace(hour=10)),
    ]

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO raw_olist.olist_orders (
                        source_file,
                        order_id,
                        order_status,
                        order_purchase_timestamp,
                        order_approved_at,
                        order_delivered_carrier_date,
                        order_delivered_customer_date
                    )
                    VALUES (
                        'pytest_fixture.csv',
                        %s,
                        'delivered',
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    orders,
                )

                result = cur.execute(
                    """
                    SELECT
                        order_id,
                        is_approval_before_purchase,
                        is_carrier_before_approval,
                        is_customer_delivery_before_carrier
                    FROM staging.stg_orders
                    WHERE order_id = ANY(%s)
                    """,
                    ([order[0] for order in orders],),
                ).fetchall()

                actual = {
                    row[0]: row[1:]
                    for row in result
                }

                assert len(actual) == 4
                assert actual[prefix + "valid"] == (False, False, False)
                assert actual[prefix + "approval"] == (True, False, False)
                assert actual[prefix + "carrier"] == (False, True, False)
                assert actual[prefix + "delivery"] == (False, False, True)
    finally:
        with get_connection() as conn:
            conn.execute(
                """
                DELETE FROM raw_olist.olist_orders
                WHERE order_id LIKE %s
                """,
                (prefix + "%",),
            )
