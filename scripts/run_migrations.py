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
        migrations.append((version, description, path))

    versions = [version for version, _, _ in migrations]
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
                        description TEXT
                    );
            """)

        for version, description, path in migrations:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT 1
                        FROM schema_migrations.applied_migrations
                        WHERE version = %s
                        """,
                        (version,),
                    )
                    if cur.fetchone():
                        print(f"Skipping {path.name}: already applied")
                        continue

                    sql = path.read_text(encoding="utf-8")
                    cur.execute(sql)
                    cur.execute(
                        """
                        INSERT INTO schema_migrations.applied_migrations
                            (version, description)
                        VALUES (%s, %s)
                        """,
                        (version, description.replace("_", " ")),
                    )

            print(f"Applied {path.name}")

    if not migrations:
        print("No migration files found.")


if __name__ == "__main__":
    main()
