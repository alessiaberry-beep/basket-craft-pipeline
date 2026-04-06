# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Basket Craft Sales Pipeline is a Python ETL pipeline that extracts order data from MySQL, transforms it into monthly sales aggregates using pure Python, and loads summaries into PostgreSQL for dashboard reporting.

## Commands

```bash
# Run the main ETL pipeline (extract → transform → load)
python pipeline.py

# Run raw data migration (copies all MySQL tables to PostgreSQL as-is)
python extract_raw.py

# Start PostgreSQL container
docker compose up -d

# Install dependencies
pip install -r requirements.txt

# Verify PostgreSQL data
docker exec basket_craft_dw psql -U postgres -d basket_craft_dw -c "SELECT COUNT(*) FROM monthly_sales_summary;"
```

## Architecture

```
MySQL (db.isba.co)          PostgreSQL (Docker/RDS)
┌─────────────────┐         ┌─────────────────────┐
│ orders          │         │ monthly_sales_summary│
│ order_items     │  ──→    │ (aggregated metrics) │
│ products        │  ETL    │                     │
│ order_item_refunds│       │ OR raw tables via   │
│ users           │         │ extract_raw.py      │
│ website_*       │         │                     │
└─────────────────┘         └─────────────────────┘
```

**Key files:**
- `pipeline.py` - Main ETL with transform logic (aggregates by month/product)
- `extract_raw.py` - Bulk migration utility using PostgreSQL COPY
- `schema.sql` - DDL for monthly_sales_summary table
- `.env` - Database credentials (MYSQL_* and PG_* variables)

## Data Processing Patterns

- **Aggregation**: Uses `defaultdict` for in-memory grouping by (year_month, product_name)
- **Currency**: `Decimal` type for financial calculations
- **Joins**: Lookup dictionaries for O(1) access (product_id→name, order_id→date)
- **Load strategy**: Full refresh (TRUNCATE + INSERT)
- **Bulk insert**: `copy_expert` with StringIO for fast PostgreSQL loading

## Configuration

Environment variables in `.env`:
- MySQL: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- PostgreSQL: `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE`

## Documentation

- Design spec: `docs/superpowers/specs/2026-04-05-sales-pipeline-design.md`
- Implementation plan: `docs/superpowers/plans/2026-04-05-sales-pipeline.md`
