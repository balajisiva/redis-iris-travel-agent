from __future__ import annotations

import hashlib
import os
import re
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Annotated, Literal

from dotenv import load_dotenv
from langcache import LangCache
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from redis_agent_memory import AgentMemory, errors, models
from typing_extensions import TypedDict
from .context_retriever import ContextRetrieverClient, extract_travel_intent


DEMO_SOURCE = "langgraph-demo"
SESSION_CONTEXT_LIMIT = 12


class MemoryCandidate(BaseModel):
    text: str = Field(description="A durable memory written as one concise sentence.")
    topics: list[str] = Field(default_factory=list)
    memory_type: Literal["semantic", "episodic"] = "semantic"


class MemoryExtraction(BaseModel):
    memories: list[MemoryCandidate] = Field(default_factory=list)


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    owner_id: str
    session_id: str
    namespace: str
    session_context: list[str]
    recalled_memories: list[str]
    extracted_memories: list[str]
    cache_hit: bool
    matched_prompt: str | None
    similarity_score: float | None
    tool_calls: list[dict]


@dataclass(frozen=True)
class DemoConfig:
    openai_model: str
    agent_memory_server_url: str
    agent_memory_store_id: str
    agent_memory_api_key: str
    langcache_server_url: str
    langcache_cache_id: str
    langcache_api_key: str
    langcache_distance_threshold: float
    context_retriever_agent_key: str | None
    owner_id: str
    namespace: str
    agent_id: str


@dataclass(frozen=True)
class TurnResult:
    session_id: str
    user_text: str
    assistant_text: str
    session_context: list[str]
    long_term_memories: list[str]
    extracted_memories: list[str]
    cache_hit: bool
    matched_prompt: str | None
    similarity_score: float | None
    tool_calls: list[dict]


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def load_config() -> DemoConfig:
    load_dotenv()
    return DemoConfig(
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        agent_memory_server_url=require_env("AGENT_MEMORY_SERVER_URL"),
        agent_memory_store_id=require_env("AGENT_MEMORY_STORE_ID"),
        agent_memory_api_key=require_env("AGENT_MEMORY_API_KEY"),
        langcache_server_url=require_env("LANGCACHE_SERVER_URL"),
        langcache_cache_id=require_env("LANGCACHE_CACHE_ID"),
        langcache_api_key=require_env("LANGCACHE_API_KEY"),
        langcache_distance_threshold=float(os.getenv("LANGCACHE_DISTANCE_THRESHOLD", "0.2")),
        context_retriever_agent_key=os.getenv("CONTEXT_RETRIEVER_AGENT_KEY"),
        owner_id=os.getenv("DEMO_OWNER_ID", "riferrei"),
        namespace=os.getenv("DEMO_NAMESPACE", "langgraph-travel-demo"),
        agent_id=os.getenv("DEMO_AGENT_ID", "travel-agent"),
    )


def now() -> datetime:
    return datetime.now(timezone.utc)


def message_text(message: AnyMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def memory_id(owner_id: str, namespace: str, text: str) -> str:
    digest = hashlib.sha256(f"{owner_id}:{namespace}:{text}".encode("utf-8")).hexdigest()
    return f"demo-{digest[:32]}"


def normalize_memory_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text.lower())).strip()


def new_session_id() -> str:
    return f"session-{uuid.uuid4().hex[:8]}"


def coerce_memories(response: object) -> list[object]:
    if isinstance(response, dict):
        return list(response.get("items", response.get("memories", [])) or [])
    items = getattr(response, "items", None)
    if items is not None:
        return list(items)
    return []


def get_memory_text(memory: object) -> str:
    if isinstance(memory, dict):
        return str(memory.get("text", ""))
    return str(getattr(memory, "text", ""))


def coerce_events(response: object) -> list[object]:
    events = getattr(response, "events", None)
    if events is None and isinstance(response, dict):
        events = response.get("events")
    return list(events or [])


def get_event_role(event: object) -> str:
    role = event.get("role") if isinstance(event, dict) else getattr(event, "role", "")
    return str(getattr(role, "value", role)).lower()


def get_event_text(event: object) -> str:
    content = event.get("content", []) if isinstance(event, dict) else getattr(event, "content", [])
    parts = []
    for item in content or []:
        if isinstance(item, dict):
            parts.append(str(item.get("text", "")))
        else:
            parts.append(str(getattr(item, "text", "")))
    return "\n".join(part for part in parts if part)


def is_not_found_error(exc: Exception) -> bool:
    return isinstance(exc, errors.NotFoundErrorResponseContent) or getattr(exc, "status_code", None) == 404


def explain_agent_memory_error(operation: str, exc: Exception) -> RuntimeError:
    hint = (
        f"Redis Agent Memory {operation} failed. Check AGENT_MEMORY_SERVER_URL, "
        "AGENT_MEMORY_STORE_ID, and AGENT_MEMORY_API_KEY. The server URL should be "
        "the Agent Memory data-plane base URL, not the PyPI/docs URL."
    )
    return RuntimeError(f"{hint}\n\nOriginal error: {exc}")


class RedisAgentMemoryService:
    def __init__(self, config: DemoConfig) -> None:
        self.config = config
        self.llm = ChatOpenAI(model=config.openai_model, temperature=0.2)
        self.extractor = self.llm.with_structured_output(MemoryExtraction)
        self.lang_cache = LangCache(
            server_url=config.langcache_server_url,
            cache_id=config.langcache_cache_id,
            api_key=config.langcache_api_key,
        )
        self.context_retriever = (
            ContextRetrieverClient(config.context_retriever_agent_key)
            if config.context_retriever_agent_key
            else None
        )

    def build_graph(self, agent_memory: AgentMemory):
        def retrieve_session_context(state: AgentState) -> dict:
            try:
                response = agent_memory.get_session_memory(session_id=state["session_id"])
            except Exception as exc:
                if is_not_found_error(exc):
                    return {"session_context": []}
                raise explain_agent_memory_error("session memory read", exc)

            session_context = []
            for event in coerce_events(response)[-SESSION_CONTEXT_LIMIT:]:
                text = get_event_text(event).strip()
                if text:
                    session_context.append(f"{get_event_role(event)}: {text}")
            return {"session_context": session_context}

        def retrieve_long_term_memories(state: AgentState) -> dict:
            last_user_message = next(
                (message for message in reversed(state["messages"]) if isinstance(message, HumanMessage)),
                None,
            )
            query = message_text(last_user_message) if last_user_message else ""

            try:
                response = agent_memory.search_long_term_memory(
                    request={
                        "text": query,
                        "limit": 5,
                        "filter": {
                            "ownerId": {"eq": state["owner_id"]},
                            "namespace": {"eq": state["namespace"]},
                        },
                        "filterOp": models.FilterConjunction.ALL,
                    }
                )
                recalled = [get_memory_text(memory) for memory in coerce_memories(response)]
            except Exception as exc:
                # Gracefully handle LTM search errors - continue with empty results
                print(f"[WARNING] LTM search failed: {exc}, continuing with empty results")
                recalled = []
            return {"recalled_memories": recalled}

        def query_context_retriever(state: AgentState) -> dict:
            """Query Context Retriever tools if travel data is needed."""
            print(f"[CONTEXT_RETRIEVER] Node called")
            print(f"[CONTEXT_RETRIEVER] Client available: {self.context_retriever is not None}")

            if not self.context_retriever:
                print("[CONTEXT_RETRIEVER] No client available, skipping")
                return {"tool_calls": []}

            last_user_message = next(
                (message for message in reversed(state["messages"]) if isinstance(message, HumanMessage)),
                None,
            )
            user_query = message_text(last_user_message) if last_user_message else ""
            print(f"[CONTEXT_RETRIEVER] User query: {user_query}")

            # Detect if we need Context Retriever
            intent = extract_travel_intent(user_query)
            print(f"[CONTEXT_RETRIEVER] Intent: {intent}")

            if not intent["needs_context_retriever"]:
                print("[CONTEXT_RETRIEVER] No travel intent detected")
                return {"tool_calls": []}

            print(f"[CONTEXT_RETRIEVER] Processing {len(intent['queries'])} queries")
            tool_calls = []
            for query in intent["queries"]:
                print(f"[CONTEXT_RETRIEVER] Calling tool for: {query}")
                query_type = query["type"]
                print(f"[CONTEXT_RETRIEVER] Query type: {query_type}")
                try:
                    if query["type"] == "search_destinations":
                        result = self.context_retriever.search_destinations(query["query"])
                        tool_calls.append({
                            "tool": "search_destination_by_text",
                            "params": {"query": query["query"]},
                            "result": result
                        })
                    elif query["type"] == "search_hotels":
                        print(f"[CONTEXT_RETRIEVER] INSIDE search_hotels handler")
                        result = self.context_retriever.search_hotels(query["query"])
                        print(f"[CONTEXT_RETRIEVER] search_hotels result: {result}")
                        tool_calls.append({
                            "tool": "search_hotel_by_text",
                            "params": {"query": query["query"]},
                            "result": result
                        })
                        print(f"[CONTEXT_RETRIEVER] Appended to tool_calls, length now: {len(tool_calls)}")
                    elif query["type"] == "search_activities":
                        result = self.context_retriever.search_activities(query["query"])
                        tool_calls.append({
                            "tool": "search_activity_by_text",
                            "params": {"query": query["query"]},
                            "result": result
                        })
                    elif query["type"] == "search_restaurants":
                        result = self.context_retriever.search_restaurants(query["query"])
                        tool_calls.append({
                            "tool": "search_restaurant_by_text",
                            "params": {"query": query["query"]},
                            "result": result
                        })
                    elif query["type"] == "filter_activities":
                        result = self.context_retriever.filter_activities_by_category(query["category"])
                        tool_calls.append({
                            "tool": "filter_activity_by_category",
                            "params": {"category": query["category"]},
                            "result": result
                        })
                except Exception as e:
                    print(f"[CONTEXT_RETRIEVER] Tool call failed: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue even if tool fails

            print(f"[CONTEXT_RETRIEVER] Returning {len(tool_calls)} tool calls")
            return {"tool_calls": tool_calls}

        def call_model(state: AgentState) -> dict:
            session_context = "\n".join(f"- {event}" for event in state["session_context"])
            if not session_context:
                session_context = "- No previous turns in this session."

            long_term_context = "\n".join(f"- {memory}" for memory in state["recalled_memories"])
            if not long_term_context:
                long_term_context = "- No relevant long-term memories found."

            # Format Context Retriever tool results
            tool_context = ""
            if state.get("tool_calls"):
                tool_results = []
                for tool_call in state["tool_calls"]:
                    tool_name = tool_call.get("tool", "unknown")
                    result = tool_call.get("result", {})
                    results_data = result.get("results", [])

                    if results_data:
                        tool_results.append(f"Tool: {tool_name}")
                        for item in results_data[:3]:  # Limit to top 3 results
                            if isinstance(item, dict):
                                name = item.get("name", "")
                                desc = item.get("description", "")
                                if name:
                                    tool_results.append(f"  - {name}: {desc}")

                if tool_results:
                    tool_context = "\n\nTravel Data from Context Retriever:\n" + "\n".join(tool_results)

            system_prompt = f"""You are a helpful travel concierge assistant.

When providing recommendations or lists, use this format:
• Hotel Name – Key feature – Price/Rating
• Hotel Name – Key feature – Price/Rating

Guidelines:
- Use bullet points (•) for multiple recommendations
- Provide 3-5 options when listing hotels or destinations
- Keep descriptions concise but informative
- Be natural and helpful

MEMORY USAGE:
- Use short-term memory (current conversation) for context
- Use long-term memory (user preferences) for personalization
- When you have data from tools, present it concisely
- Never mention "tool names", "database", or implementation details

Short-term memory (current session):
{session_context}

Long-term memories (user preferences):
{long_term_context}{tool_context}
"""
            # Get user's current message
            last_user_message = next(
                (message for message in reversed(state["messages"]) if isinstance(message, HumanMessage)),
                None,
            )
            user_prompt = message_text(last_user_message) if last_user_message else ""

            # Check LangCache first
            cache_hit = False
            matched_prompt = None
            similarity_score = None

            try:
                cache_response = self.lang_cache.search(prompt=user_prompt)
                print(f"[DEBUG] LangCache search for prompt: '{user_prompt}'")
                print(f"[DEBUG] Cache response type: {type(cache_response)}")
                print(f"[DEBUG] Cache response: {cache_response}")
                print(f"[DEBUG] Cache response dir: {dir(cache_response)}")

                # Check if we got a valid cache hit
                # LangCache returns a SearchResponse object with data attribute
                if cache_response and hasattr(cache_response, 'data'):
                    print(f"[DEBUG] Has data attribute, length: {len(cache_response.data)}")
                    if len(cache_response.data) > 0:
                        best_match = cache_response.data[0]
                        print(f"[DEBUG] Best match type: {type(best_match)}")
                        print(f"[DEBUG] Best match: {best_match}")
                        print(f"[DEBUG] Best match dir: {dir(best_match)}")

                        # Get similarity from the match (higher is better, 1.0 is perfect match)
                        similarity_score = getattr(best_match, 'similarity', 0.0)
                        print(f"[DEBUG] Similarity: {similarity_score}, Threshold: {self.config.langcache_distance_threshold}")

                        # LangCache uses similarity (higher is better), but our config is distance_threshold
                        # Convert: if similarity >= (1 - threshold), it's a hit
                        # For threshold 0.2, we want similarity >= 0.8
                        min_similarity = 1.0 - self.config.langcache_distance_threshold

                        if similarity_score >= min_similarity:
                            cache_hit = True
                            matched_prompt = getattr(best_match, 'prompt', None)
                            cached_text = getattr(best_match, 'response', None)
                            print(f"[DEBUG] CACHE HIT! Matched prompt: {matched_prompt}")
                            if cached_text:
                                response = AIMessage(content=cached_text)
                                return {
                                    "messages": [response],
                                    "cache_hit": True,
                                    "matched_prompt": matched_prompt,
                                    "similarity_score": similarity_score,
                                }
                        else:
                            print(f"[DEBUG] Similarity {similarity_score} < minimum {min_similarity}, cache miss")
                    else:
                        print(f"[DEBUG] No results in cache response")
                else:
                    print(f"[DEBUG] No cache_response or no results attribute")
            except Exception as cache_exc:
                # If cache lookup fails, continue to LLM
                print(f"LangCache search failed: {cache_exc}")
                import traceback
                traceback.print_exc()

            # Cache miss - call LLM
            response = self.llm.invoke([SystemMessage(content=system_prompt), *state["messages"]])
            assistant_text = message_text(response)

            # Save to cache
            try:
                print(f"[DEBUG] Saving to cache - prompt: '{user_prompt}', response: '{assistant_text[:100]}...'")
                save_result = self.lang_cache.set(prompt=user_prompt, response=assistant_text)
                print(f"[DEBUG] Save result: {save_result}")
            except Exception as cache_exc:
                # If cache save fails, log but continue
                print(f"LangCache save failed: {cache_exc}")
                import traceback
                traceback.print_exc()

            return {
                "messages": [response],
                "cache_hit": False,
                "matched_prompt": None,
                "similarity_score": None,
            }

        def write_memory(state: AgentState) -> dict:
            user_message = next(
                (message for message in reversed(state["messages"]) if isinstance(message, HumanMessage)),
                None,
            )
            assistant_message = next(
                (message for message in reversed(state["messages"]) if isinstance(message, AIMessage)),
                None,
            )
            if user_message is None or assistant_message is None:
                return {"extracted_memories": []}

            user_text = message_text(user_message)
            assistant_text = message_text(assistant_message)

            try:
                agent_memory.add_session_event(
                    session_id=state["session_id"],
                    actor_id=state["owner_id"],
                    role=models.MessageRole.USER,
                    content=[{"text": user_text}],
                    created_at=now(),
                    metadata={"source": DEMO_SOURCE},
                )
                agent_memory.add_session_event(
                    session_id=state["session_id"],
                    actor_id=self.config.agent_id,
                    role=models.MessageRole.ASSISTANT,
                    content=[{"text": assistant_text}],
                    created_at=now(),
                    metadata={"source": DEMO_SOURCE},
                )
            except Exception as exc:
                raise explain_agent_memory_error("session event write", exc)

            extraction = self.extractor.invoke(
                [
                    SystemMessage(
                        content=(
                            "Extract only durable user facts, persistent preferences, and stable constraints "
                            "that the user explicitly states in the current message and that should help in future "
                            "unrelated sessions. Do not extract active task details, current itinerary details, "
                            "dates, destinations, booking requests, or other context that only matters for this "
                            "conversation unless the user explicitly asks to remember it for later. Do not extract "
                            "anything that is only mentioned by the assistant or already present in existing "
                            "long-term memories. "
                            "If the message is a short reply, a confirmation, a single word, a number, or only "
                            "makes sense in the context of the current conversation, return an empty list.\n\n"
                            "Examples of messages that should produce NO memories:\n"
                            "- '1st' (a date fragment answering a question)\n"
                            "- 'yes' (a confirmation)\n"
                            "- 'no', 'ok', 'sure', 'sounds good' (short replies)\n"
                            "- 'June 15th' (a date answering a question)\n"
                            "- 'New York' (a destination answering a question)\n"
                            "- 'I am planning a trip to Lisbon next month' (transient travel plan)\n\n"
                            "Examples of messages that SHOULD produce memories:\n"
                            "- 'My name is Ricardo' → 'The user's name is Ricardo.'\n"
                            "- 'I always fly Delta' → 'The user prefers to fly Delta Airlines.'\n"
                            "- 'I am vegetarian' → 'The user is vegetarian.'\n"
                            "- 'I have two kids, a 3-year-old and a newborn' → 'The user has two kids: a newborn and a 3-year-old.'\n"
                            "- 'yes, remember that I prefer window seats for next time' → 'The user prefers window seats.' (extract the confirmed fact, not the confirmation itself)\n"
                            "- 'I always stay at Marriott hotels and I need a room in Paris next week' → 'The user prefers Marriott hotels.' (extract the preference, ignore the transient request)\n"
                        )
                    ),
                    HumanMessage(
                        content=(
                            f"Current user message:\n{user_text}\n\n"
                            "Existing long-term memories:\n"
                            + "\n".join(f"- {memory}" for memory in state["recalled_memories"])
                        )
                    ),
                ]
            )

            records = []
            extracted_texts = []
            known_memory_texts = {
                normalize_memory_text(memory)
                for memory in state["recalled_memories"]
            }
            accepted_memory_texts = set(known_memory_texts)
            for memory in extraction.memories:
                text = memory.text.strip()
                if not text:
                    continue
                normalized_text = normalize_memory_text(text)
                if not normalized_text or normalized_text in accepted_memory_texts:
                    continue
                accepted_memory_texts.add(normalized_text)
                record_id = memory_id(state["owner_id"], state["namespace"], text)
                extracted_texts.append(text)
                records.append(
                    {
                        "id": record_id,
                        "text": text,
                        "ownerId": state["owner_id"],
                        "namespace": state["namespace"],
                        "sessionId": state["session_id"],
                        "topics": memory.topics or ["travel"],
                        "memoryType": memory.memory_type,
                    }
                )

            if records:
                try:
                    agent_memory.bulk_create_long_term_memories(memories=records)
                except Exception as exc:
                    raise explain_agent_memory_error("long-term memory write", exc)
            return {"extracted_memories": extracted_texts}

        builder = StateGraph(AgentState)
        builder.add_node("retrieve_session_context", retrieve_session_context)
        builder.add_node("retrieve_long_term_memories", retrieve_long_term_memories)
        builder.add_node("query_context_retriever", query_context_retriever)
        builder.add_node("call_model", call_model)
        builder.add_node("write_memory", write_memory)
        builder.add_edge(START, "retrieve_session_context")
        builder.add_edge("retrieve_session_context", "retrieve_long_term_memories")
        builder.add_edge("retrieve_long_term_memories", "query_context_retriever")
        builder.add_edge("query_context_retriever", "call_model")
        builder.add_edge("call_model", "write_memory")
        builder.add_edge("write_memory", END)
        return builder.compile()

    def run_turn(self, agent_memory: AgentMemory, session_id: str, user_text: str) -> TurnResult:
        graph = self.build_graph(agent_memory)
        state = graph.invoke(
            {
                "messages": [HumanMessage(content=user_text)],
                "owner_id": self.config.owner_id,
                "session_id": session_id,
                "namespace": self.config.namespace,
                "session_context": [],
                "recalled_memories": [],
                "extracted_memories": [],
                "cache_hit": False,
                "matched_prompt": None,
                "similarity_score": None,
                "tool_calls": [],
            }
        )
        assistant_message = next(
            (message for message in reversed(state["messages"]) if isinstance(message, AIMessage)),
            None,
        )
        return TurnResult(
            session_id=session_id,
            user_text=user_text,
            assistant_text=message_text(assistant_message) if assistant_message else "",
            session_context=state["session_context"],
            long_term_memories=state["recalled_memories"],
            extracted_memories=state["extracted_memories"],
            cache_hit=state.get("cache_hit", False),
            matched_prompt=state.get("matched_prompt"),
            similarity_score=state.get("similarity_score"),
            tool_calls=state.get("tool_calls", []),
        )

    def read_session_context(self, agent_memory: AgentMemory, session_id: str) -> list[str]:
        try:
            response = agent_memory.get_session_memory(session_id=session_id)
        except Exception as exc:
            if is_not_found_error(exc):
                return []
            raise explain_agent_memory_error("session memory read", exc)

        session_context = []
        for event in coerce_events(response)[-SESSION_CONTEXT_LIMIT:]:
            text = get_event_text(event).strip()
            if text:
                session_context.append(f"{get_event_role(event)}: {text}")
        return session_context

    def delete_session_memory(self, agent_memory: AgentMemory, session_id: str) -> None:
        try:
            agent_memory.delete_session_memory(session_id=session_id)
        except Exception as exc:
            if not is_not_found_error(exc):
                raise explain_agent_memory_error("session memory delete", exc)
