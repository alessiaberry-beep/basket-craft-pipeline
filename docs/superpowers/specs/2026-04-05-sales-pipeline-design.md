# Basket Craft Sales Pipeline Design

**Date:** 2026-04-05
**Status:** Approved

## Overview

Build a data pipeline to populate a monthly sales dashboard for Basket Craft. The pipeline extracts order data from MySQL, transforms it in Python, and loads aggregated metrics into PostgreSQL.

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   .env      │────▶│   pipeline.py   │────▶│   PostgreSQL    │
│  (config)   │     │  (Pure Python)  │     │   (Docker)      │
└─────────────┘     └────────┬────────┘     └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │     MySQL       │
                    │  basket_craft   │
                    └─────────────────┘
```

### Data Flow

1. **Extract** — Pull raw data from MySQL:
   - `orders` (32K rows)
   - `order_items` (40K rows)
   - `products` (4 rows)
   - `order_item_refunds` (1.7K rows)

2. **Transform** — Aggregate in Python:
   - Build product lookup dict (product_id → product_name)
   - Build refunds lookup dict (order_item_id → refund_amount)
   - Join order_items with orders to get timestamps
   - Group by (year_month, product_name)
   - Calculate: order_count, gross_revenue, refund_amount, net_revenue, avg_order_value

3. **Load** — Write to PostgreSQL:
   - TRUNCATE `monthly_sales_summary`
   - INSERT aggregated rows (~150 rows)

## Source Database

**MySQL Database:** `basket_craft` at `db.isba.co:3306`

### Tables Used

| Table | Rows | Key Columns |
|-------|------|-------------|
| `orders` | 32,313 | order_id, created_at, user_id, price_usd |
| `order_items` | 40,025 | order_item_id, order_id, product_id, price_usd |
| `products` | 4 | product_id, product_name |
| `order_item_refunds` | 1,731 | order_item_id, refund_amount_usd |

### Products

| ID | Name | Price |
|----|------|-------|
| 1 | The Original Gift Basket | $49.99 |
| 2 | The Valentine's Gift Basket | $59.99 |
| 3 | The Birthday Gift Basket | $45.99 |
| 4 | The Holiday Gift Basket | $29.99 |

### Date Range

Orders span March 2023 to March 2026 (3 years of data).

## Destination Database

**PostgreSQL:** Running in Docker, database `basket_craft_dw`

### Output Table: `monthly_sales_summary`

```sql
CREATE TABLE monthly_sales_summary (
    year_month      VARCHAR(7)      NOT NULL,
    product_name    VARCHAR(50)     NOT NULL,
    order_count     INTEGER         NOT NULL,
    gross_revenue   NUMERIC(12,2)   NOT NULL,
    refund_amount   NUMERIC(12,2)   NOT NULL,
    net_revenue     NUMERIC(12,2)   NOT NULL,
    avg_order_value NUMERIC(10,2)   NOT NULL,
    PRIMARY KEY (year_month, product_name)
);
```

### Column Definitions

| Column | Description |
|--------|-------------|
| `year_month` | Format "YYYY-MM" (e.g., "2026-03") |
| `product_name` | Product category name |
| `order_count` | Count of distinct orders containing this product |
| `gross_revenue` | Sum of `order_items.price_usd` for this product |
| `refund_amount` | Sum of refunds for order items of this product |
| `net_revenue` | `gross_revenue - refund_amount` |
| `avg_order_value` | `net_revenue / order_count` |

## Configuration

All credentials stored in `.env` file (gitignored):

```bash
# MySQL Source
MYSQL_HOST=db.isba.co
MYSQL_PORT=3306
MYSQL_USER=analyst
MYSQL_PASSWORD=<secret>
MYSQL_DATABASE=basket_craft

# PostgreSQL Destination
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_DATABASE=basket_craft_dw
```

Loaded via `python-dotenv`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
mysql_host = os.environ['MYSQL_HOST']
```

## Project Structure

```
basket-craft-pipeline/
├── pipeline.py          # Main ETL script
├── docker-compose.yml   # PostgreSQL container definition
├── schema.sql           # PostgreSQL DDL
├── requirements.txt     # pymysql, psycopg2-binary, python-dotenv
├── .env                 # Credentials (gitignored)
├── .gitignore
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-04-05-sales-pipeline-design.md
```

## Technical Decisions

### Approach: Python-Heavy

All transformation logic runs in Python rather than SQL. This means:

- Extract raw tables from MySQL (all ~75K rows)
- Build in-memory data structures (dicts, sets)
- Aggregate using `collections.defaultdict`
- Load final results to PostgreSQL

**Rationale:** User preference for pure Python. Keeps all logic in one language, easier to debug step-by-step.

### Refresh Strategy: Full

Each pipeline run:
1. Extracts all source data
2. Performs full aggregation
3. TRUNCATEs destination table
4. INSERTs all rows

**Rationale:** Simplicity. With ~150 output rows, full refresh is fast and guarantees consistency.

### Trigger: Manual

Run via command line:

```bash
python pipeline.py
```

**Rationale:** User will run on-demand when dashboard data needs updating.

## Dependencies

```
pymysql>=1.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```

No pandas, no SQLAlchemy — pure Python with minimal dependencies.

## Transform Logic

```python
from collections import defaultdict
from decimal import Decimal

# 1. Build lookups
products = {row['product_id']: row['product_name'] for row in products_data}
refunds = defaultdict(Decimal)
for row in refunds_data:
    refunds[row['order_item_id']] = row['refund_amount_usd']

# 2. Build order timestamp lookup
order_months = {}
for row in orders_data:
    order_months[row['order_id']] = row['created_at'].strftime('%Y-%m')

# 3. Aggregate
summary = defaultdict(lambda: {'orders': set(), 'gross': Decimal('0'), 'refunds': Decimal('0')})

for item in order_items_data:
    year_month = order_months[item['order_id']]
    product_name = products[item['product_id']]
    key = (year_month, product_name)

    summary[key]['orders'].add(item['order_id'])
    summary[key]['gross'] += item['price_usd']
    summary[key]['refunds'] += refunds.get(item['order_item_id'], Decimal('0'))

# 4. Calculate final metrics
results = []
for (year_month, product_name), data in summary.items():
    order_count = len(data['orders'])
    gross_revenue = data['gross']
    refund_amount = data['refunds']
    net_revenue = gross_revenue - refund_amount
    avg_order_value = net_revenue / order_count if order_count > 0 else Decimal('0')

    results.append((
        year_month,
        product_name,
        order_count,
        gross_revenue,
        refund_amount,
        net_revenue,
        avg_order_value
    ))
```

## Dashboard Metrics Delivered

| Metric | Description | Business Use |
|--------|-------------|--------------|
| Revenue (Gross) | Total sales before refunds | Track sales volume |
| Revenue (Net) | Sales minus refunds | True revenue |
| Order Count | Distinct orders per product | Demand analysis |
| Avg Order Value | Net revenue per order | Customer value |

All metrics available by:
- Month (YYYY-MM)
- Product category (4 products)

## Future Considerations

Not in scope but could be added later:
- Incremental refresh (track last run timestamp)
- Scheduling via cron
- Additional dimensions (user segments, marketing channels)
- Web analytics integration (sessions, pageviews tables)
