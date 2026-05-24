#!/usr/bin/env python3
"""Quick test of Redis Cloud connection."""

import os
import sys
import redis
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test Redis Cloud connection."""
    print("Testing Redis Cloud Connection...")
    print("=" * 60)

    host = os.getenv('REDIS_HOST')
    port = int(os.getenv('REDIS_PORT', '6379'))
    password = os.getenv('REDIS_PASSWORD')
    ssl = os.getenv('REDIS_SSL', 'true').lower() == 'true'

    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"SSL: {ssl}")
    print(f"Password: {'*' * len(password) if password else 'None'}")
    print()

    try:
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            ssl=ssl,
            decode_responses=True,
        )

        # Test ping
        print("Testing PING...", end=" ")
        result = r.ping()
        print(f"✓ {result}")

        # Test write
        print("Testing SET...", end=" ")
        r.set('test:connection', 'success')
        print("✓ OK")

        # Test read
        print("Testing GET...", end=" ")
        value = r.get('test:connection')
        print(f"✓ {value}")

        # Test delete
        print("Testing DEL...", end=" ")
        r.delete('test:connection')
        print("✓ OK")

        print()
        print("=" * 60)
        print("✓ All tests passed! Redis Cloud is ready.")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nPlease check:")
        print("  1. REDIS_HOST is correct")
        print("  2. REDIS_PORT is correct")
        print("  3. REDIS_PASSWORD is correct")
        print("  4. Your IP is whitelisted in Redis Cloud")
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
