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
