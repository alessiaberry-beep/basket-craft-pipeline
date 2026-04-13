#!/usr/bin/env python3
"""
Snowflake Loader: PostgreSQL → Snowflake

Reads all tables from PostgreSQL RDS and loads them into
Snowflake basket_craft.raw schema using write_pandas.
"""

import os
import pandas as pd
import psycopg2
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL configuration
PG_CONFIG = {
    'host': os.environ['PG_HOST'],
    'port': int(os.environ['PG_PORT']),
    'user': os.environ['PG_USER'],
    'password': os.environ['PG_PASSWORD'],
    'dbname': os.environ['PG_DATABASE'],
}

# Snowflake configuration
SNOWFLAKE_CONFIG = {
    'account': os.environ['SNOWFLAKE_ACCOUNT'],
    'user': os.environ['SNOWFLAKE_USER'],
    'password': os.environ['SNOWFLAKE_PASSWORD'],
    'role': os.environ['SNOWFLAKE_ROLE'],
    'warehouse': os.environ['SNOWFLAKE_WAREHOUSE'],
    'database': os.environ['SNOWFLAKE_DATABASE'],
    'schema': os.environ['SNOWFLAKE_SCHEMA'],
}


def get_pg_tables(pg_conn):
    """Get list of all user tables in PostgreSQL public schema."""
    query = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """
    with pg_conn.cursor() as cur:
        cur.execute(query)
        return [row[0] for row in cur.fetchall()]


def extract_table_to_dataframe(pg_conn, table_name):
    """Extract a PostgreSQL table into a pandas DataFrame."""
    query = f'SELECT * FROM "{table_name}"'
    return pd.read_sql(query, pg_conn)


def load_table_to_snowflake(sf_conn, df, table_name):
    """Load a DataFrame into Snowflake, replacing existing data."""
    if df.empty:
        print(f"    → 0 rows (empty table)", flush=True)
        return 0

    # write_pandas with auto_create_table replaces the table
    success, num_chunks, num_rows, _ = write_pandas(
        conn=sf_conn,
        df=df,
        table_name=table_name.upper(),  # snowflake stores unquoted as uppercase
        auto_create_table=True,
        overwrite=True,
        quote_identifiers=False,
    )

    if success:
        print(f"    → {num_rows:,} rows loaded", flush=True)
    else:
        print(f"    → FAILED to load", flush=True)

    return num_rows if success else 0


def main():
    """Main pipeline: PostgreSQL → Snowflake."""
    print("=" * 60, flush=True)
    print("Snowflake Loader: PostgreSQL → Snowflake", flush=True)
    print("=" * 60, flush=True)

    # Connect to PostgreSQL
    print("\n📥 Connecting to PostgreSQL...", flush=True)
    pg_conn = psycopg2.connect(**PG_CONFIG)
    print(f"   Connected to {PG_CONFIG['host']}/{PG_CONFIG['dbname']}", flush=True)

    # Connect to Snowflake
    print("\n📤 Connecting to Snowflake...", flush=True)
    sf_conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    print(f"   Connected to {SNOWFLAKE_CONFIG['account']}", flush=True)
    print(f"   Database: {SNOWFLAKE_CONFIG['database']}.{SNOWFLAKE_CONFIG['schema']}", flush=True)

    # Get all tables from PostgreSQL
    tables = get_pg_tables(pg_conn)
    print(f"\n📋 Found {len(tables)} tables to load:", flush=True)
    for t in tables:
        print(f"   - {t}", flush=True)

    # Extract and load each table
    print("\n🔄 Extracting and loading tables...", flush=True)
    total_rows = 0
    for table_name in tables:
        print(f"  Loading {table_name}...", flush=True)

        # Extract from PostgreSQL
        df = extract_table_to_dataframe(pg_conn, table_name)

        # Load to Snowflake
        rows = load_table_to_snowflake(sf_conn, df, table_name)
        total_rows += rows

    # Cleanup
    pg_conn.close()
    sf_conn.close()

    print("\n" + "=" * 60, flush=True)
    print(f"✅ Complete! Loaded {total_rows:,} total rows across {len(tables)} tables", flush=True)
    print("=" * 60, flush=True)


if __name__ == '__main__':
    main()
