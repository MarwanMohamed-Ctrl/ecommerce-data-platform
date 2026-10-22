import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path("data/raw/olist")

# Candidate keys based on the source dataset's intended grain.
CANDIDATE_KEYS = {
    "olist_customers_dataset.csv": ("customer_id",),
    "olist_orders_dataset.csv": ("order_id",),
    "olist_order_items_dataset.csv": ("order_id", "order_item_id"),
    "olist_order_payments_dataset.csv": (
        "order_id", "payment_sequential"
    ),
    "olist_order_reviews_dataset.csv": ("review_id",),
    "olist_products_dataset.csv": ("product_id",),
    "olist_sellers_dataset.csv": ("seller_id",),
    "product_category_name_translation.csv": (
        "product_category_name",
    ),
}


def profile_file(path: Path) -> None:
    row_count = 0
    blank_counts = Counter()
    malformed_rows = 0
    key_counts = Counter()
    duplicate_key_rows = 0

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        columns = reader.fieldnames or []
        key_columns = CANDIDATE_KEYS.get(path.name)

        if key_columns and not set(key_columns).issubset(columns):
            raise ValueError(
                f"{path.name}: expected key columns {key_columns}"
            )

        for row in reader:
            row_count += 1

            if None in row:
                malformed_rows += 1

            for column in columns:
                value = row.get(column)
                if value is None or value.strip() == "":
                    blank_counts[column] += 1

            if key_columns:
                key = tuple(row.get(column) for column in key_columns)

                if any(value is None or value == "" for value in key):
                    continue

                key_counts[key] += 1
                if key_counts[key] == 2:
                    duplicate_key_rows += 2
                elif key_counts[key] > 2:
                    duplicate_key_rows += 1

    print(f"\nFILE: {path.name}")
    print(f"CSV records: {row_count:,}")
    print(f"Columns ({len(columns)}): {', '.join(columns)}")
    print(f"Rows with extra fields: {malformed_rows:,}")

    if blank_counts:
        print("Blank values:")
        for column, count in sorted(blank_counts.items()):
            print(f"  {column}: {count:,}")
    else:
        print("Blank values: none")

    if key_columns:
        print(f"Candidate key: {key_columns}")
        print(f"Distinct nonblank keys: {len(key_counts):,}")
        print(f"Rows participating in duplicate keys: "
              f"{duplicate_key_rows:,}")
    else:
        print("Candidate key: not assigned (inspect grain first)")


def main() -> None:
    if not DATA_DIR.is_dir():
        raise SystemExit(f"Data directory not found: {DATA_DIR}")

    files = sorted(DATA_DIR.glob("*.csv"))
    if not files:
        raise SystemExit(f"No CSV files found in {DATA_DIR}")

    for path in files:
        profile_file(path)


if __name__ == "__main__":
    main()
