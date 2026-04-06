#!/usr/bin/env python3
"""
Raw Data Extraction: MySQL → PostgreSQL

Extracts all tables from MySQL basket_craft database and loads them
as-is into PostgreSQL RDS with no transformations.
"""

import os
import sys
import io
import pymysql
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

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

# MySQL to PostgreSQL type mapping
TYPE_MAP = {
    'int': 'INTEGER',
    'bigint': 'BIGINT',
    'smallint': 'SMALLINT',
    'tinyint': 'SMALLINT',
    'float': 'REAL',
    'double': 'DOUBLE PRECISION',
    'decimal': 'DECIMAL',
    'varchar': 'VARCHAR',
    'char': 'CHAR',
    'text': 'TEXT',
    'mediumtext': 'TEXT',
    'longtext': 'TEXT',
    'datetime': 'TIMESTAMP',
    'timestamp': 'TIMESTAMP',
    'date': 'DATE',
    'time': 'TIME',
    'blob': 'BYTEA',
    'mediumblob': 'BYTEA',
    'longblob': 'BYTEA',
    'boolean': 'BOOLEAN',
    'bit': 'BOOLEAN',
}


def get_mysql_tables(cursor):
    """Get list of all tables in MySQL database."""
    cursor.execute("SHOW TABLES")
    return [row[0] for row in cursor.fetchall()]


def get_mysql_schema(cursor, table_name):
    """Get column definitions for a MySQL table."""
    cursor.execute(f"DESCRIBE `{table_name}`")
    columns = []
    for row in cursor.fetchall():
        col_name = row[0]
        col_type = row[1].lower()
        is_nullable = row[2] == 'YES'
        columns.append({
            'name': col_name,
            'type': col_type,
            'nullable': is_nullable,
        })
    return columns


def mysql_to_pg_type(mysql_type):
    """Convert MySQL type to PostgreSQL type."""
    # Extract base type and size
    base_type = mysql_type.split('(')[0].strip()

    # Handle unsigned integers
    base_type = base_type.replace(' unsigned', '')

    if base_type in TYPE_MAP:
        pg_type = TYPE_MAP[base_type]
        # Preserve size for varchar/char/decimal
        if '(' in mysql_type and base_type in ('varchar', 'char', 'decimal'):
            size = mysql_type[mysql_type.index('('):mysql_type.index(')')+1]
            pg_type = pg_type + size
        return pg_type

    # Default to TEXT for unknown types
    return 'TEXT'


def create_pg_table(pg_cursor, table_name, columns):
    """Create a PostgreSQL table matching the MySQL schema."""
    col_defs = []
    for col in columns:
        pg_type = mysql_to_pg_type(col['type'])
        nullable = '' if col['nullable'] else ' NOT NULL'
        col_defs.append(f'"{col["name"]}" {pg_type}{nullable}')

    # Drop existing table and create new one
    pg_cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
        sql.Identifier(table_name)
    ))

    create_sql = f'CREATE TABLE "{table_name}" ({", ".join(col_defs)})'
    pg_cursor.execute(create_sql)


def extract_and_load_table(mysql_cursor, pg_conn, pg_cursor, table_name):
    """Extract data from MySQL table and load into PostgreSQL using COPY."""
    # Get schema
    columns = get_mysql_schema(mysql_cursor, table_name)
    col_names = [col['name'] for col in columns]

    # Create PostgreSQL table
    print(f"  Creating table {table_name}...", flush=True)
    create_pg_table(pg_cursor, table_name, columns)
    pg_conn.commit()

    # Extract data from MySQL
    mysql_cursor.execute(f"SELECT * FROM `{table_name}`")
    rows = mysql_cursor.fetchall()

    if not rows:
        print(f"    → 0 rows (empty table)", flush=True)
        return 0

    # Build CSV in memory for fast COPY
    buffer = io.StringIO()
    for row in rows:
        line = '\t'.join(
            '\\N' if v is None else str(v).replace('\\', '\\\\').replace('\t', '\\t').replace('\n', '\\n').replace('\r', '\\r')
            for v in row
        )
        buffer.write(line + '\n')
    buffer.seek(0)

    # Use COPY for fast bulk insert
    col_names_quoted = ', '.join([f'"{c}"' for c in col_names])
    pg_cursor.copy_expert(f'COPY "{table_name}" ({col_names_quoted}) FROM STDIN', buffer)
    pg_conn.commit()

    print(f"    → {len(rows):,} rows loaded", flush=True)
    return len(rows)


def main():
    """Main extraction pipeline."""
    print("=" * 60, flush=True)
    print("Raw Data Extraction: MySQL → PostgreSQL", flush=True)
    print("=" * 60, flush=True)

    # Connect to MySQL
    print("\n📥 Connecting to MySQL...", flush=True)
    mysql_conn = pymysql.connect(**MYSQL_CONFIG)
    mysql_cursor = mysql_conn.cursor()
    print(f"   Connected to {MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}", flush=True)

    # Connect to PostgreSQL
    print("\n📤 Connecting to PostgreSQL...", flush=True)
    pg_conn = psycopg2.connect(**PG_CONFIG)
    pg_cursor = pg_conn.cursor()
    print(f"   Connected to {PG_CONFIG['host']}/{PG_CONFIG['dbname']}", flush=True)

    # Get all tables
    tables = get_mysql_tables(mysql_cursor)
    print(f"\n📋 Found {len(tables)} tables to extract:", flush=True)
    for t in tables:
        print(f"   - {t}", flush=True)

    # Extract and load each table
    print("\n🔄 Extracting and loading tables...", flush=True)
    total_rows = 0
    for table in tables:
        rows = extract_and_load_table(mysql_cursor, pg_conn, pg_cursor, table)
        total_rows += rows

    # Cleanup
    mysql_cursor.close()
    mysql_conn.close()
    pg_cursor.close()
    pg_conn.close()

    print("\n" + "=" * 60, flush=True)
    print(f"✅ Complete! Loaded {total_rows:,} total rows across {len(tables)} tables", flush=True)
    print("=" * 60, flush=True)


if __name__ == '__main__':
    main()
