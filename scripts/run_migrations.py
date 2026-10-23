
import hashlib
import os
import re
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "sql" / "migrations"
VERSION_PATTERN = re.compile(r"^(\d{3})_.+\.sql$")


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


def discover_migrations():
    migrations = []

    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        match = VERSION_PATTERN.match(path.name)
        if not match:
            raise ValueError(
                f"Invalid migration filename: {path.name}. "
                "Expected format: 001_description.sql"
            )

        version = match.group(1)
        description = path.stem[len(version) + 1:]
        checksum = hashlib.sha256(path.read_bytes()).hexdigest()
        migrations.append((version, description, path, checksum))

    versions = [version for version, _, _, _ in migrations]
    if len(versions) != len(set(versions)):
        raise ValueError("Duplicate migration versions found.")

    return migrations


def main():
    if not MIGRATIONS_DIR.is_dir():
        raise SystemExit(f"Migration directory not found: {MIGRATIONS_DIR}")

    migrations = discover_migrations()

    with connect_to_postgres() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE SCHEMA IF NOT EXISTS schema_migrations;

                CREATE TABLE IF NOT EXISTS
                    schema_migrations.applied_migrations (
                        version VARCHAR(100) PRIMARY KEY,
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        description TEXT,
                        checksum CHAR(64)
                    );
            """)
            cur.execute("""
                ALTER TABLE schema_migrations.applied_migrations
                ADD COLUMN IF NOT EXISTS checksum CHAR(64);
            """)

        for version, description, path, checksum in migrations:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT checksum
                        FROM schema_migrations.applied_migrations
                        WHERE version = %s
                        """,
                        (version,),
                    )
                    row = cur.fetchone()

                    if row:
                        stored_checksum = row[0]

                        if stored_checksum is None:
                            # Backfill history for migrations recorded before
                            # checksum support was introduced.
                            cur.execute(
                                """
                                UPDATE schema_migrations.applied_migrations
                                SET checksum = %s
                                WHERE version = %s
                                  AND checksum IS NULL
                                """,
                                (checksum, version),
                            )
                            print(
                                f"Recorded baseline checksum for {path.name}"
                            )
                        elif stored_checksum.strip() != checksum:
                            raise RuntimeError(
                                f"Checksum mismatch for applied migration "
                                f"{path.name}. Do not edit an applied "
                                "migration; create a new migration instead."
                            )
                        else:
                            print(
                                f"Skipping {path.name}: already applied "
                                "and checksum matches"
                            )
                        continue

                    sql = path.read_text(encoding="utf-8")

                    if version == "001":
                        sql = sql.removeprefix("BEGIN;\n").removesuffix("COMMIT;\n")

                    cur.execute(sql)
                    cur.execute(
                        """
                        INSERT INTO schema_migrations.applied_migrations
                            (version, description, checksum)
                        VALUES (%s, %s, %s)
                        """,
                        (
                            version,
                            description.replace("_", " "),
                            checksum,
                        ),
                    )

            print(f"Applied {path.name}")

    if not migrations:
        print("No migration files found.")


if __name__ == "__main__":
    main()
