# E-commerce Data Engineering Platform

A production-style Data Engineering portfolio project demonstrating reliable
batch and streaming pipelines, data quality, orchestration, and analytics.

## Goals

- Ingest data from REST APIs and PostgreSQL.
- Build incremental, restartable batch pipelines.
- Store raw and processed data in Parquet.
- Orchestrate workflows with Apache Airflow.
- Process batch and streaming data with Apache Spark.
- Stream events through Apache Kafka.
- Model analytics using dbt and a dimensional warehouse.
- Test data quality and automate checks through CI/CD.
- Document architecture, performance, and operational recovery.

## Planned Architecture

Sources -> Ingestion -> Raw Data Lake -> Processing
         -> Analytical Warehouse -> dbt Models -> Dashboard

Streaming Events -> Kafka -> Spark Structured Streaming
                 -> Analytical Storage

## Development Environment

- Fedora Linux
- Docker Engine and Docker Compose
- PostgreSQL
- Git and GitHub

## Project Status

Initial foundation. The database schema, ingestion pipelines, and analytics
models have not yet been implemented.

## Local Setup

1. Install Docker Engine and the Docker Compose plugin.
2. Copy `.env.example` to `.env` if `.env` does not already exist.
3. Set a strong local database password in `.env`.
4. Start services using `docker compose up -d`.
5. Check service health using `docker compose ps`.

Never commit `.env`, credentials, or real customer data.

## Testing

Testing instructions will be documented as each component is implemented.
