#!/usr/bin/env python3
"""
RDI stand-in: sync PostgreSQL data into Redis Cloud.

Redis Data Integration (RDI) is still in preview and not generally available,
so this script stands in for it: it reads from PostgreSQL and writes JSON
documents into Redis in the shape Context Retriever reads from. It is NOT a
re-implementation of RDI's change-data-capture — just enough to give the
pipeline fresh data for the demo. Swap it for real RDI once you have access.
"""

import os
import sys
import psycopg2
import redis
from dotenv import load_dotenv
from typing import Dict, List, Any
import json

load_dotenv()

# Database connections
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'port': int(os.getenv('POSTGRES_PORT', '5432')),
    'database': os.getenv('POSTGRES_DB', 'traveldb'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres'),
}

REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST'),
    'port': int(os.getenv('REDIS_PORT', '6379')),
    'password': os.getenv('REDIS_PASSWORD'),
    'ssl': os.getenv('REDIS_SSL', 'true').lower() == 'true',
}

# Table definitions with key patterns
TABLES = [
    {
        'name': 'destinations',
        'key_prefix': 'destination',
        'id_column': 'id',
    },
    {
        'name': 'hotels',
        'key_prefix': 'hotel',
        'id_column': 'id',
    },
    {
        'name': 'activities',
        'key_prefix': 'activity',
        'id_column': 'id',
    },
    {
        'name': 'restaurants',
        'key_prefix': 'restaurant',
        'id_column': 'id',
    },
    {
        'name': 'user_preferences',
        'key_prefix': 'user_preference',
        'id_column': 'id',
    },
]


def connect_postgres():
    """Connect to PostgreSQL database."""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        print(f"✓ Connected to PostgreSQL at {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}")
        return conn
    except Exception as e:
        print(f"✗ Failed to connect to PostgreSQL: {e}")
        sys.exit(1)


def connect_redis():
    """Connect to Redis Cloud."""
    try:
        r = redis.Redis(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            password=REDIS_CONFIG['password'],
            ssl=REDIS_CONFIG['ssl'],
            decode_responses=True,
        )
        r.ping()
        print(f"✓ Connected to Redis at {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
        return r
    except Exception as e:
        print(f"✗ Failed to connect to Redis: {e}")
        sys.exit(1)


def postgres_array_to_list(pg_array: str) -> List[str]:
    """Convert PostgreSQL array string to Python list."""
    if not pg_array or pg_array == '{}':
        return []
    # Remove curly braces and split by comma
    cleaned = pg_array.strip('{}')
    if not cleaned:
        return []
    return [item.strip('"').strip() for item in cleaned.split(',')]


def convert_value(value: Any) -> str:
    """Convert PostgreSQL value to Redis-compatible string."""
    if value is None:
        return ''
    if isinstance(value, (list, tuple)):
        # Convert arrays to JSON strings for Redis
        return json.dumps(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
        # Handle PostgreSQL array strings
        return json.dumps(postgres_array_to_list(value))
    return str(value)


def sync_table(pg_conn, redis_conn, table_config: Dict):
    """Sync a single table from PostgreSQL to Redis."""
    table_name = table_config['name']
    key_prefix = table_config['key_prefix']
    id_column = table_config['id_column']

    print(f"\n📊 Syncing table: {table_name}")

    cursor = pg_conn.cursor()

    # Get column names
    cursor.execute(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    columns = [row[0] for row in cursor.fetchall()]

    # Fetch all rows
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()

    synced_count = 0
    for row in rows:
        # Create a dictionary of column: value
        record = dict(zip(columns, row))

        # Get the ID for the Redis key
        record_id = record[id_column]
        redis_key = f"{key_prefix}:{record_id}"

        # Convert all values to JSON-compatible format
        redis_data = {}
        for col, val in record.items():
            if val is not None:
                # Convert to JSON-compatible types
                if isinstance(val, (list, dict)):
                    redis_data[col] = val
                else:
                    redis_data[col] = str(val)

        # Store as Redis JSON document (required by Context Retriever)
        redis_conn.json().set(redis_key, '$', redis_data)
        synced_count += 1

    cursor.close()
    print(f"  ✓ Synced {synced_count} records from {table_name}")
    return synced_count


def verify_sync(redis_conn):
    """Verify data was synced correctly."""
    print("\n✅ Verification:")

    for table_config in TABLES:
        pattern = f"{table_config['key_prefix']}:*"
        keys = list(redis_conn.scan_iter(match=pattern, count=100))
        print(f"  • {table_config['name']}: {len(keys)} records")

        # Show sample record
        if keys:
            sample_key = keys[0]
            sample_data = redis_conn.json().get(sample_key)
            print(f"    Sample: {sample_key}")
            if isinstance(sample_data, dict):
                for k, v in list(sample_data.items())[:3]:
                    print(f"      {k}: {v}")


def main():
    """Main sync function."""
    print("=" * 60)
    print("RDI stand-in — PostgreSQL → Redis Cloud sync")
    print("(RDI is in preview; this stands in for it for the demo)")
    print("=" * 60)

    # Check required environment variables
    if not REDIS_CONFIG['host']:
        print("✗ Error: REDIS_HOST not set in .env")
        sys.exit(1)

    # Connect to databases
    pg_conn = connect_postgres()
    redis_conn = connect_redis()

    try:
        # Sync all tables
        total_synced = 0
        for table_config in TABLES:
            count = sync_table(pg_conn, redis_conn, table_config)
            total_synced += count

        # Verify
        verify_sync(redis_conn)

        print("\n" + "=" * 60)
        print(f"✓ Sync complete! Total records synced: {total_synced}")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Go to Redis Cloud → Context Retriever")
        print("2. Create a Surface pointing to this Redis database")
        print("3. Run 'Auto-detect' — Context Retriever creates the JSON indexes")
        print("4. It then auto-generates the MCP tools from the data")
        print("=" * 60)

    finally:
        pg_conn.close()
        redis_conn.close()


if __name__ == '__main__':
    main()
