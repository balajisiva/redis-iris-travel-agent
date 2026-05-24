#!/usr/bin/env python3
"""
Check status of IRIS services (Agent Memory and LangCache).
"""

import os
import sys
from dotenv import load_dotenv
from redis_agent_memory import AgentMemory
from langcache import LangCache

load_dotenv()

def check_agent_memory():
    """Check Agent Memory service status."""
    print("=" * 60)
    print("Checking Agent Memory...")
    print("=" * 60)

    try:
        agent_memory = AgentMemory(
            server_url=os.getenv("AGENT_MEMORY_SERVER_URL"),
            store_id=os.getenv("AGENT_MEMORY_STORE_ID"),
            api_key=os.getenv("AGENT_MEMORY_API_KEY"),
        )

        # Try to search (this will fail if index is missing)
        print("\nTrying LTM search...")
        try:
            response = agent_memory.search_long_term_memory(
                request={
                    "text": "test query",
                    "limit": 1,
                }
            )
            print("✓ Agent Memory LTM search working")
            print(f"  Response type: {type(response)}")
        except Exception as e:
            print(f"✗ Agent Memory LTM search failed: {e}")
            print("\n  This likely means the index was deleted during Redis upgrade.")
            print("  The SDK should auto-create indexes on first write.")
            print("  Try creating a new long-term memory to trigger index creation.")

        # Try session memory
        print("\nTrying session memory...")
        try:
            response = agent_memory.get_session_memory(session_id="test-session")
            print("✓ Agent Memory session memory working")
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print("✓ Agent Memory session memory endpoint accessible (session not found is expected)")
            else:
                print(f"✗ Agent Memory session memory failed: {e}")

    except Exception as e:
        print(f"✗ Failed to initialize Agent Memory: {e}")
        return False

    return True


def check_langcache():
    """Check LangCache service status."""
    print("\n" + "=" * 60)
    print("Checking LangCache...")
    print("=" * 60)

    try:
        lang_cache = LangCache(
            server_url=os.getenv("LANGCACHE_SERVER_URL"),
            cache_id=os.getenv("LANGCACHE_CACHE_ID"),
            api_key=os.getenv("LANGCACHE_API_KEY"),
        )

        # Try to search
        print("\nTrying cache search...")
        try:
            response = lang_cache.search(prompt="test query")
            print("✓ LangCache search working")
            print(f"  Response type: {type(response)}")
            if hasattr(response, 'data'):
                print(f"  Results: {len(response.data)}")
        except Exception as e:
            print(f"✗ LangCache search failed: {e}")
            print("\n  This likely means the index was deleted during Redis upgrade.")
            print("  Try saving a cache entry to trigger index creation:")
            try:
                result = lang_cache.set(prompt="test prompt", response="test response")
                print(f"  ✓ Successfully wrote test cache entry: {result}")
                print("  Try searching again...")
                response = lang_cache.search(prompt="test prompt")
                print(f"  ✓ LangCache search now working!")
            except Exception as e2:
                print(f"  ✗ Failed to create test cache entry: {e2}")

    except Exception as e:
        print(f"✗ Failed to initialize LangCache: {e}")
        return False

    return True


def main():
    print("\nIRIS Services Status Check")
    print("Testing Agent Memory and LangCache connectivity and indexes\n")

    agent_memory_ok = check_agent_memory()
    langcache_ok = check_langcache()

    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    print(f"Agent Memory: {'✓ OK' if agent_memory_ok else '✗ ISSUES'}")
    print(f"LangCache: {'✓ OK' if langcache_ok else '✗ ISSUES'}")
    print("=" * 60)

    if not (agent_memory_ok and langcache_ok):
        print("\nRecommendation:")
        print("  The indexes may have been deleted during Redis Cloud upgrade.")
        print("  The demo will still work, but you'll see warnings in logs.")
        print("  Indexes should auto-recreate on first write operations.")
        sys.exit(1)


if __name__ == "__main__":
    main()
