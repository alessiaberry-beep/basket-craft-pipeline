# Basket Craft Sales Pipeline

ETL pipeline that extracts order data from the Basket Craft MySQL database, transforms it into monthly sales aggregates, and loads it into PostgreSQL for dashboard reporting.

## Data Sources

### MySQL Source (Read-Only)
- **Host:** `db.isba.co:3306`
- **Database:** `basket_craft`
- **Tables:** orders, order_items, products, order_item_refunds, users, employees, website_sessions, website_pageviews

### AWS RDS PostgreSQL (Raw Data)
- **Host:** `basket-craft-db.cmh4q2cqkqj9.us-east-1.rds.amazonaws.com`
- **Database:** `basket_craft`
- **Region:** us-east-1

Contains raw copies of all MySQL tables for direct querying:

| Table | Rows |
|-------|-----:|
| employees | 20 |
| order_item_refunds | 1,731 |
| order_items | 40,025 |
| orders | 32,313 |
| products | 4 |
| users | 31,696 |
| website_pageviews | 1,188,124 |
| website_sessions | 472,871 |

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure credentials in `.env`:
   ```
   MYSQL_HOST=db.isba.co
   MYSQL_PORT=3306
   MYSQL_USER=analyst
   MYSQL_PASSWORD=<password>
   MYSQL_DATABASE=basket_craft

   PG_HOST=basket-craft-db.cmh4q2cqkqj9.us-east-1.rds.amazonaws.com
   PG_PORT=5432
   PG_USER=student
   PG_PASSWORD=<password>
   PG_DATABASE=basket_craft
   ```

## Usage

### Extract Raw Data to RDS
Copies all MySQL tables to AWS RDS PostgreSQL as-is (no transformations):
```bash
python extract_raw.py
```

### Run Sales Pipeline
Extracts, transforms to monthly aggregates, and loads to PostgreSQL:
```bash
python pipeline.py
```

### Query RDS Directly
```bash
psql -h basket-craft-db.cmh4q2cqkqj9.us-east-1.rds.amazonaws.com -U student -d basket_craft
```

## Project Structure

```
basket-craft-pipeline/
├── pipeline.py        # Main ETL with monthly aggregation
├── extract_raw.py     # Raw MySQL → PostgreSQL migration
├── schema.sql         # DDL for monthly_sales_summary
├── requirements.txt   # Python dependencies
├── docker-compose.yml # Local PostgreSQL (optional)
└── .env               # Database credentials
```
