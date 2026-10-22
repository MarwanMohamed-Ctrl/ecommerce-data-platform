from scripts.load_olist_raw import connect_to_postgres


def main():
    checks = [
	{
            "name": "Raw orders have unique, non-empty IDs",
            "query": """
                SELECT COUNT(*) - COUNT(DISTINCT NULLIF(order_id, ''))
                FROM raw_olist.olist_orders
            """,
            "expected": 0,
            "severity": "FAIL",
        },
        {
            "name": "Staging orders match raw orders",
            "query": """
                SELECT
                    (SELECT COUNT(*) FROM staging.stg_orders)
                    -
                    (SELECT COUNT(*) FROM raw_olist.olist_orders)
            """,
            "expected": 0,
            "severity": "FAIL",
        },
        {
            "name": "Duplicate order IDs",
            "query": """
                SELECT COUNT(*) - COUNT(DISTINCT order_id)
                FROM staging.stg_orders
            """,
            "expected": 0,
            "severity": "FAIL",
        },
        {
            "name": "Missing order IDs",
            "query": """
                SELECT COUNT(*)
                FROM staging.stg_orders
                WHERE order_id IS NULL
            """,
            "expected": 0,
            "severity": "FAIL",
        },
        {
            "name": "Approval before purchase",
            "query": """
                SELECT COUNT(*)
                FROM staging.stg_orders
                WHERE is_approval_before_purchase IS TRUE
            """,
            "expected": 0,
            "severity": "FAIL",
        },
        {
            "name": "Carrier before approval",
            "query": """
                SELECT COUNT(*)
                FROM staging.stg_orders
                WHERE is_carrier_before_approval IS TRUE
            """,
            "expected": 0,
            "severity": "WARN",
        },
        {
            "name": "Customer delivery before carrier",
            "query": """
                SELECT COUNT(*)
                FROM staging.stg_orders
                WHERE is_customer_delivery_before_carrier IS TRUE
            """,
            "expected": 0,
            "severity": "WARN",
        },
        {
            "name": "Delivered orders missing delivery date",
            "query": """
                SELECT COUNT(*)
                FROM staging.stg_orders
                WHERE order_status = 'delivered'
                  AND order_delivered_customer_date IS NULL
            """,
            "expected": 0,
            "severity": "WARN",
        },
    ]

    failures = 0
    warnings = 0

    with connect_to_postgres() as conn:
        for check in checks:
            with conn.cursor() as cur:
                cur.execute(check["query"])
                actual = cur.fetchone()[0]

            passed = actual == check["expected"]

            if passed:
                status = "PASS"
            else:
                status = check["severity"]

                if status == "FAIL":
                    failures += 1
                else:
                    warnings += 1

            print(
                f"[{status}] {check['name']}: "
                f"actual={actual:,}, expected={check['expected']:,}"
            )

    print(
        f"\nSummary: {len(checks) - failures - warnings} passed, "
        f"{warnings} warnings, {failures} failures."
    )

    if failures:
        raise SystemExit(1)

    print("Data-quality checks completed successfully.")


if __name__ == "__main__":
    main()
