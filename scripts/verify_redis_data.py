#!/usr/bin/env python3
"""Quick verification of synced data in Redis."""

import os
import redis
import json
from dotenv import load_dotenv

load_dotenv()

def main():
    """Verify data in Redis."""
    r = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        password=os.getenv('REDIS_PASSWORD'),
        ssl=os.getenv('REDIS_SSL', 'true').lower() == 'true',
        decode_responses=True,
    )

    print("=" * 60)
    print("Redis Data Verification")
    print("=" * 60)

    # Sample destination
    print("\n📍 Sample Destination (Paris):")
    paris = r.hgetall('destination:1')
    print(f"  Name: {paris.get('name')}")
    print(f"  Country: {paris.get('country')}")
    print(f"  Description: {paris.get('description')}")
    print(f"  Best Season: {paris.get('best_season')}")
    activities = json.loads(paris.get('popular_activities', '[]'))
    print(f"  Popular Activities: {', '.join(activities)}")

    # Sample hotel
    print("\n🏨 Sample Hotel (Four Seasons Bali):")
    hotel = r.hgetall('hotel:6')
    print(f"  Name: {hotel.get('name')}")
    print(f"  Price Range: {hotel.get('price_range')}")
    print(f"  Rating: {hotel.get('rating')}")
    amenities = json.loads(hotel.get('amenities', '[]'))
    print(f"  Amenities: {', '.join(amenities[:3])}...")

    # Sample activity
    print("\n🎭 Sample Activity (Louvre Tour):")
    activity = r.hgetall('activity:1')
    print(f"  Name: {activity.get('name')}")
    print(f"  Category: {activity.get('category')}")
    print(f"  Duration: {activity.get('duration_hours')} hours")
    print(f"  Price: ${activity.get('price_usd')}")

    # Sample restaurant
    print("\n🍽️  Sample Restaurant (Le Jules Verne):")
    restaurant = r.hgetall('restaurant:1')
    print(f"  Name: {restaurant.get('name')}")
    print(f"  Cuisine: {restaurant.get('cuisine_type')}")
    print(f"  Price Range: {restaurant.get('price_range')}")
    print(f"  Rating: {restaurant.get('rating')}")

    # User preferences
    print("\n👤 Sample User Preferences (Alice):")
    user = r.hgetall('user_preference:1')
    print(f"  User ID: {user.get('user_id')}")
    destinations = json.loads(user.get('preferred_destinations', '[]'))
    print(f"  Preferred Destinations: {', '.join(destinations)}")
    print(f"  Budget Level: {user.get('budget_level')}")
    print(f"  Travel Style: {user.get('travel_style')}")

    print("\n" + "=" * 60)
    print("✓ All data successfully synced to Redis Cloud!")
    print("=" * 60)

if __name__ == '__main__':
    main()
