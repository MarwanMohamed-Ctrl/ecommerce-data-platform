from scripts.load_olist_raw import connect_to_postgres


def main():
    checks = [
        (
            "Total orders",
            """
            SELECT COUNT(*)
            FROM staging.stg_orders
            """,
            99_441,
        ),
        (
            "Duplicate order IDs",
            """
            SELECT COUNT(*) - COUNT(DISTINCT order_id)
            FROM staging.stg_orders
            """,
            0,
        ),
        (
            "Missing order IDs",
            """
            SELECT COUNT(*)
            FROM staging.stg_orders
            WHERE order_id IS NULL
            """,
            0,
        ),
        (
            "Approval before purchase",
            """
            SELECT COUNT(*)
            FROM staging.stg_orders
            WHERE is_approval_before_purchase IS TRUE
            """,
            0,
        ),
    ]

    failures = 0

    with connect_to_postgres() as conn:
        for name, query, expected in checks:
            with conn.cursor() as cur:
                cur.execute(query)
                actual = cur.fetchone()[0]

            passed = actual == expected
            status = "PASS" if passed else "FAIL"

            print(
                f"[{status}] {name}: "
                f"actual={actual:,}, expected={expected:,}"
            )

            if not passed:
                failures += 1

    if failures:
        raise SystemExit(f"\n{failures} data-quality check(s) failed.")

    print(f"\nAll {len(checks)} data-quality checks passed.")


if __name__ == "__main__":
    main()
