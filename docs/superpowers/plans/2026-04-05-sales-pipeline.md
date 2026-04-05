# Sales Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an ETL pipeline that extracts order data from MySQL, transforms it in Python, and loads monthly sales summaries into PostgreSQL.

**Architecture:** Python-heavy ETL with full refresh strategy. Extract 4 tables (~75K rows) from MySQL, aggregate in-memory using dicts, load ~150 summary rows to PostgreSQL. All credentials from `.env` file.

**Tech Stack:** Python 3, pymysql, psycopg2-binary, python-dotenv, Docker Compose (PostgreSQL 16)

---

## File Structure

| File | Purpose |
|------|---------|
| `docker-compose.yml` | PostgreSQL container definition |
| `schema.sql` | DDL for `monthly_sales_summary` table |
| `requirements.txt` | Python dependencies |
| `.env` | Database credentials (update with PG vars) |
| `pipeline.py` | Main ETL script: extract, transform, load |

---

## Task 1: PostgreSQL Infrastructure

**Files:**
- Create: `docker-compose.yml`
- Create: `schema.sql`

- [ ] **Step 1: Create docker-compose.yml**

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    container_name: basket_craft_dw
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: basket_craft_dw
    ports:
      - "5432:5432"
    volumes:
      - basket_craft_data:/var/lib/postgresql/data
      - ./schema.sql:/docker-entrypoint-initdb.d/schema.sql

volumes:
  basket_craft_data:
```

- [ ] **Step 2: Create schema.sql**

```sql
-- Monthly sales summary table for Basket Craft dashboard
CREATE TABLE IF NOT EXISTS monthly_sales_summary (
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

- [ ] **Step 3: Start PostgreSQL container**

Run:
```bash
docker compose up -d
```

Expected: Container `basket_craft_dw` starts, PostgreSQL available on port 5432.

- [ ] **Step 4: Verify table was created**

Run:
```bash
docker exec basket_craft_dw psql -U postgres -d basket_craft_dw -c "\dt"
```

Expected:
```
 Schema |         Name          | Type  |  Owner
--------+-----------------------+-------+----------
 public | monthly_sales_summary | table | postgres
```

- [ ] **Step 5: Commit infrastructure files**

```bash
git add docker-compose.yml schema.sql
git commit -m "feat: add PostgreSQL infrastructure

- Docker Compose config for PostgreSQL 16
- Schema for monthly_sales_summary table"
```

---

## Task 2: Python Dependencies & Environment

**Files:**
- Create: `requirements.txt`
- Modify: `.env`

- [ ] **Step 1: Create requirements.txt**

```
pymysql>=1.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```

- [ ] **Step 2: Install dependencies**

Run:
```bash
pip install -r requirements.txt
```

Expected: All packages install successfully.

- [ ] **Step 3: Update .env with PostgreSQL credentials**

Add to `.env`:
```bash
# PostgreSQL Destination
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=postgres
PG_DATABASE=basket_craft_dw
```

- [ ] **Step 4: Verify .env has all required variables**

Run:
```bash
python3 -c "
from dotenv import load_dotenv
import os
load_dotenv()
required = ['MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE',
            'PG_HOST', 'PG_PORT', 'PG_USER', 'PG_PASSWORD', 'PG_DATABASE']
for var in required:
    val = os.environ.get(var)
    status = '✓' if val else '✗ MISSING'
    print(f'{var}: {status}')
"
```

Expected: All variables show ✓.

- [ ] **Step 5: Commit requirements**

```bash
git add requirements.txt
git commit -m "feat: add Python dependencies

- pymysql for MySQL extraction
- psycopg2-binary for PostgreSQL loading
- python-dotenv for config management"
```

---

## Task 3: Pipeline Script - Extract Functions

**Files:**
- Create: `pipeline.py`

- [ ] **Step 1: Create pipeline.py with imports and config loading**

```python
#!/usr/bin/env python3
"""
Basket Craft Sales Pipeline

Extracts order data from MySQL, transforms to monthly aggregates,
and loads into PostgreSQL for dashboard reporting.
"""

import os
from collections import defaultdict
from decimal import Decimal

import pymysql
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MySQL configuration
MYSQL_CONFIG = {
    'host': os.environ['MYSQL_HOST'],
    'port': int(os.environ['MYSQL_PORT']),
    'user': os.environ['MYSQL_USER'],
    'password': os.environ['MYSQL_PASSWORD'],
    'database': os.environ['MYSQL_DATABASE'],
}

# PostgreSQL configuration
PG_CONFIG = {
    'host': os.environ['PG_HOST'],
    'port': int(os.environ['PG_PORT']),
    'user': os.environ['PG_USER'],
    'password': os.environ['PG_PASSWORD'],
    'dbname': os.environ['PG_DATABASE'],
}
```

- [ ] **Step 2: Add extract functions**

Append to `pipeline.py`:

```python
def extract_from_mysql():
    """Extract raw data from MySQL source tables."""
    print("Connecting to MySQL...")
    conn = pymysql.connect(**MYSQL_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    cursor = conn.cursor()

    # Extract products
    print("  Extracting products...")
    cursor.execute("SELECT product_id, product_name FROM products")
    products = cursor.fetchall()
    print(f"    → {len(products)} products")

    # Extract orders
    print("  Extracting orders...")
    cursor.execute("SELECT order_id, created_at FROM orders")
    orders = cursor.fetchall()
    print(f"    → {len(orders)} orders")

    # Extract order items
    print("  Extracting order_items...")
    cursor.execute("SELECT order_item_id, order_id, product_id, price_usd FROM order_items")
    order_items = cursor.fetchall()
    print(f"    → {len(order_items)} order items")

    # Extract refunds
    print("  Extracting order_item_refunds...")
    cursor.execute("SELECT order_item_id, refund_amount_usd FROM order_item_refunds")
    refunds = cursor.fetchall()
    print(f"    → {len(refunds)} refunds")

    conn.close()
    print("MySQL extraction complete.\n")

    return {
        'products': products,
        'orders': orders,
        'order_items': order_items,
        'refunds': refunds,
    }
```

- [ ] **Step 3: Test extract function**

Run:
```bash
python3 -c "
from pipeline import extract_from_mysql
data = extract_from_mysql()
print('Products:', len(data['products']))
print('Orders:', len(data['orders']))
print('Order Items:', len(data['order_items']))
print('Refunds:', len(data['refunds']))
"
```

Expected:
```
Connecting to MySQL...
  Extracting products...
    → 4 products
  Extracting orders...
    → 32313 orders
  Extracting order_items...
    → 40025 order items
  Extracting order_item_refunds...
    → 1731 refunds
MySQL extraction complete.

Products: 4
Orders: 32313
Order Items: 40025
Refunds: 1731
```

- [ ] **Step 4: Commit extract functions**

```bash
git add pipeline.py
git commit -m "feat: add MySQL extraction functions

- Load config from .env
- Extract products, orders, order_items, refunds
- Use DictCursor for named column access"
```

---

## Task 4: Pipeline Script - Transform Function

**Files:**
- Modify: `pipeline.py`

- [ ] **Step 1: Add transform function**

Append to `pipeline.py`:

```python
def transform(data):
    """Transform raw data into monthly sales summary."""
    print("Transforming data...")

    # 1. Build product lookup
    products = {row['product_id']: row['product_name'] for row in data['products']}
    print(f"  Built product lookup: {len(products)} products")

    # 2. Build refunds lookup
    refunds = defaultdict(Decimal)
    for row in data['refunds']:
        refunds[row['order_item_id']] = Decimal(str(row['refund_amount_usd']))
    print(f"  Built refunds lookup: {len(refunds)} refunds")

    # 3. Build order month lookup
    order_months = {}
    for row in data['orders']:
        order_months[row['order_id']] = row['created_at'].strftime('%Y-%m')
    print(f"  Built order month lookup: {len(order_months)} orders")

    # 4. Aggregate by (year_month, product_name)
    summary = defaultdict(lambda: {
        'orders': set(),
        'gross': Decimal('0'),
        'refunds': Decimal('0'),
    })

    for item in data['order_items']:
        order_id = item['order_id']
        product_id = item['product_id']
        order_item_id = item['order_item_id']
        price = Decimal(str(item['price_usd']))

        year_month = order_months[order_id]
        product_name = products[product_id]
        key = (year_month, product_name)

        summary[key]['orders'].add(order_id)
        summary[key]['gross'] += price
        summary[key]['refunds'] += refunds.get(order_item_id, Decimal('0'))

    print(f"  Aggregated into {len(summary)} month-product combinations")

    # 5. Calculate final metrics
    results = []
    for (year_month, product_name), agg in summary.items():
        order_count = len(agg['orders'])
        gross_revenue = agg['gross']
        refund_amount = agg['refunds']
        net_revenue = gross_revenue - refund_amount
        avg_order_value = net_revenue / order_count if order_count > 0 else Decimal('0')

        results.append({
            'year_month': year_month,
            'product_name': product_name,
            'order_count': order_count,
            'gross_revenue': gross_revenue,
            'refund_amount': refund_amount,
            'net_revenue': net_revenue,
            'avg_order_value': avg_order_value,
        })

    # Sort by year_month, then product_name
    results.sort(key=lambda r: (r['year_month'], r['product_name']))

    print(f"Transform complete: {len(results)} summary rows.\n")
    return results
```

- [ ] **Step 2: Test transform function**

Run:
```bash
python3 -c "
from pipeline import extract_from_mysql, transform
data = extract_from_mysql()
results = transform(data)
print('Sample output (first 3 rows):')
for row in results[:3]:
    print(f\"  {row['year_month']} | {row['product_name'][:25]:<25} | orders={row['order_count']:>4} | net=\${row['net_revenue']:>10,.2f}\")
"
```

Expected output showing first 3 summary rows with correct aggregations.

- [ ] **Step 3: Commit transform function**

```bash
git add pipeline.py
git commit -m "feat: add transform function

- Build lookup dicts for products, refunds, order months
- Aggregate by (year_month, product_name)
- Calculate order_count, gross/net revenue, AOV
- Use Decimal for precise currency math"
```

---

## Task 5: Pipeline Script - Load Function

**Files:**
- Modify: `pipeline.py`

- [ ] **Step 1: Add load function**

Append to `pipeline.py`:

```python
def load_to_postgres(results):
    """Load transformed data into PostgreSQL."""
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()

    # Truncate existing data (full refresh)
    print("  Truncating monthly_sales_summary...")
    cursor.execute("TRUNCATE TABLE monthly_sales_summary")

    # Insert new data
    print(f"  Inserting {len(results)} rows...")
    insert_sql = """
        INSERT INTO monthly_sales_summary
        (year_month, product_name, order_count, gross_revenue, refund_amount, net_revenue, avg_order_value)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    for row in results:
        cursor.execute(insert_sql, (
            row['year_month'],
            row['product_name'],
            row['order_count'],
            row['gross_revenue'],
            row['refund_amount'],
            row['net_revenue'],
            row['avg_order_value'],
        ))

    conn.commit()
    conn.close()
    print("PostgreSQL load complete.\n")
```

- [ ] **Step 2: Add main function**

Append to `pipeline.py`:

```python
def main():
    """Run the full ETL pipeline."""
    print("=" * 50)
    print("Basket Craft Sales Pipeline")
    print("=" * 50 + "\n")

    # Extract
    data = extract_from_mysql()

    # Transform
    results = transform(data)

    # Load
    load_to_postgres(results)

    # Summary
    print("=" * 50)
    print("Pipeline completed successfully!")
    print(f"  Loaded {len(results)} rows to monthly_sales_summary")
    print("=" * 50)


if __name__ == '__main__':
    main()
```

- [ ] **Step 3: Run the complete pipeline**

Run:
```bash
python pipeline.py
```

Expected:
```
==================================================
Basket Craft Sales Pipeline
==================================================

Connecting to MySQL...
  Extracting products...
    → 4 products
  Extracting orders...
    → 32313 orders
  Extracting order_items...
    → 40025 order items
  Extracting order_item_refunds...
    → 1731 refunds
MySQL extraction complete.

Transforming data...
  Built product lookup: 4 products
  Built refunds lookup: 1731 refunds
  Built order month lookup: 32313 orders
  Aggregated into ~120 month-product combinations
Transform complete: ~120 summary rows.

Connecting to PostgreSQL...
  Truncating monthly_sales_summary...
  Inserting ~120 rows...
PostgreSQL load complete.

==================================================
Pipeline completed successfully!
  Loaded ~120 rows to monthly_sales_summary
==================================================
```

- [ ] **Step 4: Commit load function and main**

```bash
git add pipeline.py
git commit -m "feat: add load function and main entry point

- TRUNCATE + INSERT for full refresh
- Main function orchestrates extract → transform → load
- Progress output for visibility"
```

---

## Task 6: Verification & Final Commit

**Files:**
- None (verification only)

- [ ] **Step 1: Verify row count in PostgreSQL**

Run:
```bash
docker exec basket_craft_dw psql -U postgres -d basket_craft_dw -c "SELECT COUNT(*) FROM monthly_sales_summary;"
```

Expected: ~120 rows (37 months × 1-4 products per month, depending on launch dates).

- [ ] **Step 2: Verify sample data**

Run:
```bash
docker exec basket_craft_dw psql -U postgres -d basket_craft_dw -c "
SELECT year_month, product_name, order_count, net_revenue, avg_order_value
FROM monthly_sales_summary
ORDER BY year_month DESC, net_revenue DESC
LIMIT 10;"
```

Expected: Recent months showing all 4 products with reasonable revenue figures.

- [ ] **Step 3: Verify highest revenue product matches exploratory analysis**

Run:
```bash
docker exec basket_craft_dw psql -U postgres -d basket_craft_dw -c "
SELECT product_name, SUM(net_revenue) as total_net_revenue
FROM monthly_sales_summary
GROUP BY product_name
ORDER BY total_net_revenue DESC;"
```

Expected: "The Original Gift Basket" has highest total (~$1.2M gross, slightly less net after refunds).

- [ ] **Step 4: Verify month with most orders**

Run:
```bash
docker exec basket_craft_dw psql -U postgres -d basket_craft_dw -c "
SELECT year_month, SUM(order_count) as total_orders
FROM monthly_sales_summary
GROUP BY year_month
ORDER BY total_orders DESC
LIMIT 5;"
```

Expected: December 2025 has most orders (~2,300).

- [ ] **Step 5: Final commit with all files**

```bash
git status
git add -A
git commit -m "feat: complete sales pipeline implementation

ETL pipeline extracts from MySQL basket_craft, transforms in Python,
and loads monthly sales summaries to PostgreSQL.

- 4 source tables → 1 summary table
- Full refresh strategy (TRUNCATE + INSERT)
- ~120 rows covering 37 months of data
- All credentials loaded from .env"
```

- [ ] **Step 6: Push to GitHub**

```bash
git push
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | PostgreSQL Infrastructure | docker-compose.yml, schema.sql |
| 2 | Python Dependencies | requirements.txt, .env |
| 3 | Extract Functions | pipeline.py |
| 4 | Transform Function | pipeline.py |
| 5 | Load Function | pipeline.py |
| 6 | Verification | (queries only) |

**Total estimated time:** 20-30 minutes

**Final deliverable:** Running `python pipeline.py` extracts from MySQL, transforms in Python, and loads to PostgreSQL. Dashboard can query `monthly_sales_summary` for revenue, order counts, and AOV by month and product.
