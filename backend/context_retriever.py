"""Context Retriever tool integration for LangGraph agent."""

import os
import httpx
from typing import Any


class ContextRetrieverClient:
    """Simple client for calling Context Retriever tools."""

    def __init__(self, agent_key: str):
        self.agent_key = agent_key
        # Use the Context Surfaces MCP endpoint
        self.base_url = "https://gcp-us-east4.context-surfaces.redis.io/mcp"
        self.headers = {
            "X-API-Key": agent_key,
            "Content-Type": "application/json",
        }

    def call_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """Call a Context Retriever tool using MCP JSON-RPC 2.0 protocol."""
        # MCP uses JSON-RPC 2.0 format
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": kwargs
            },
            "id": 1
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.base_url, json=payload, headers=self.headers)
                response.raise_for_status()
                rpc_response = response.json()

                # Extract result from JSON-RPC response
                if "result" in rpc_response and "content" in rpc_response["result"]:
                    content = rpc_response["result"]["content"]
                    if content and len(content) > 0 and "text" in content[0]:
                        import json
                        return json.loads(content[0]["text"])

                return {"results": [], "count": 0}
        except httpx.HTTPStatusError as e:
            return {
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "results": []
            }
        except Exception as e:
            return {
                "error": str(e),
                "results": []
            }

    def search_destinations(self, query: str, limit: int = 3) -> dict[str, Any]:
        """Search for destinations by text."""
        return self.call_tool("search_destination_by_text", query=query, limit=limit)

    def filter_hotels_by_price(self, price_range: str, limit: int = 3) -> dict[str, Any]:
        """Filter hotels by price range."""
        return self.call_tool("filter_hotel_by_price_range", value=price_range, limit=limit)

    def search_hotels(self, query: str, limit: int = 3) -> dict[str, Any]:
        """Search for hotels by text."""
        return self.call_tool("search_hotel_by_text", query=query, limit=limit)

    def search_activities(self, query: str, limit: int = 3) -> dict[str, Any]:
        """Search for activities by text."""
        return self.call_tool("search_activity_by_text", query=query, limit=limit)

    def search_restaurants(self, query: str, limit: int = 3) -> dict[str, Any]:
        """Search for restaurants by text."""
        return self.call_tool("search_restaurant_by_text", query=query, limit=limit)

    def filter_activities_by_category(self, category: str, limit: int = 3) -> dict[str, Any]:
        """Filter activities by category."""
        return self.call_tool("filter_activity_by_category", value=category, limit=limit)

    def get_destination_by_id(self, destination_id: str) -> dict[str, Any]:
        """Get a specific destination by ID."""
        return self.call_tool("get_destination_by_id", id=destination_id)

    def filter_destination_by_country(self, country: str, limit: int = 3) -> dict[str, Any]:
        """Filter destinations by country."""
        return self.call_tool("filter_destination_by_country", value=country, limit=limit)


def extract_travel_intent(user_message: str) -> dict[str, Any]:
    """Simple heuristic to detect if user is asking about travel data."""
    message_lower = user_message.lower()

    intent = {
        "needs_context_retriever": False,
        "queries": []
    }

    # Check for destination queries
    if any(word in message_lower for word in ["destination", "place", "visit", "go to", "travel to", "city", "country"]):
        if any(word in message_lower for word in ["beach", "mountain", "warm", "cold", "europe", "asia"]):
            intent["needs_context_retriever"] = True
            # Extract search query
            intent["queries"].append({
                "type": "search_destinations",
                "query": user_message
            })

    # Check for hotel queries
    if any(word in message_lower for word in ["hotel", "stay", "accommodation", "resort", "where to stay"]):
        intent["needs_context_retriever"] = True

        # Extract location terms for text search
        location_terms = []
        for term in ["barcelona", "paris", "tokyo", "london", "rome", "lisbon", "porto", "madrid"]:
            if term in message_lower:
                location_terms.append(term)

        # Use location-based search (text search works on name, address fields)
        # Note: price_range is included in results, LLM will filter luxury/budget in response
        if location_terms:
            search_query = " ".join(location_terms)
            intent["queries"].append({"type": "search_hotels", "query": search_query})
        else:
            # No specific location, search with full message
            intent["queries"].append({"type": "search_hotels", "query": user_message})

    # Check for activity queries
    if any(word in message_lower for word in ["activity", "activities", "do", "things to do", "attraction"]):
        intent["needs_context_retriever"] = True
        if "cultural" in message_lower or "museum" in message_lower:
            intent["queries"].append({"type": "filter_activities", "category": "cultural"})
        elif "food" in message_lower or "dining" in message_lower:
            intent["queries"].append({"type": "filter_activities", "category": "food"})
        elif "nature" in message_lower or "outdoor" in message_lower:
            intent["queries"].append({"type": "filter_activities", "category": "nature"})
        else:
            intent["queries"].append({"type": "search_activities", "query": user_message})

    # Check for restaurant queries
    if any(word in message_lower for word in ["restaurant", "eat", "dining", "food", "cuisine"]):
        intent["needs_context_retriever"] = True
        intent["queries"].append({"type": "search_restaurants", "query": user_message})

    return intent
