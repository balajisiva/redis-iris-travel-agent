# Redis Iris Travel Agent

A LangGraph travel-concierge agent built to evaluate [Redis Iris](https://redis.io/iris/) — wiring up Agent Memory, LangCache, and Context Retriever into one production-style pipeline, with every layer surfaced as a live panel so you can watch it work.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

> **Background:** I wrote up what I found building this — what a production agent actually needs, and how Iris held up over a weekend. [Read the post →](REPLACE_WITH_BLOG_URL)

---

## What this is

A production agent needs four things that have nothing to do with the model: memory within a session, memory across sessions, real and fresh data, and cost control. You normally build and maintain all four yourself.

This project tests whether Redis Iris can handle them as services instead. It uses a travel concierge as the example domain, but the patterns are domain-agnostic — adapt them to customer support, e-commerce, documentation assistants, or any agent.

It started from Redis's official [redis-agent-memory-with-langgraph-demo](https://github.com/redis-developer/redis-agent-memory-with-langgraph-demo), which demonstrates **Agent Memory** only. This extends that foundation with **LangCache**, **Context Retriever**, a real PostgreSQL data layer, and a UI that shows all the layers at once.

### Iris components used

- 🧠 **Agent Memory** — session memory (STM) and cross-session long-term memory (LTM)
- ⚡ **LangCache** — semantic response caching with a configurable similarity threshold
- 🔧 **Context Retriever** — 15 MCP tools auto-generated from the data schema, no API code
- 🔄 **RDI** — Redis Data Integration for database→Redis sync. RDI is still in preview and not generally available (you contact Redis to evaluate it), so this repo uses a small stand-in sync script in its place.

---

## Quick Start

### Prerequisites

- Docker & Docker Compose
- A Redis Cloud account ([free tier available](https://redis.io/cloud))
- An OpenAI API key (or compatible LLM provider)

### 1. Clone and set up

```bash
git clone https://github.com/balajisiva/redis-iris-travel-agent
cd redis-iris-travel-agent

cp .env.example .env
```

### 2. Configure Iris services

In [Redis Cloud](https://redis.io/cloud), create an Agent Memory store, a LangCache instance, and a Context Retriever Surface, then fill in `.env`:

```bash
# Agent Memory
AGENT_MEMORY_SERVER_URL=https://<region>.memory.redis.io
AGENT_MEMORY_STORE_ID=your-store-id
AGENT_MEMORY_API_KEY=your-api-key

# LangCache
LANGCACHE_SERVER_URL=https://<region>.langcache.redis.io
LANGCACHE_CACHE_ID=your-cache-id
LANGCACHE_API_KEY=your-api-key

# Context Retriever
CONTEXT_RETRIEVER_AGENT_KEY=your-agent-key

# LLM provider
OPENAI_API_KEY=your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview
```

### 3. Run it

```bash
docker-compose up -d

# Sync sample data into Redis (stand-in for RDI)
docker-compose exec backend python scripts/simulate_rdi.py

# Run the demo flow
./demo_flow.sh

# Or open the web UI
open http://localhost:8080
```

> **Note on a cold start:** on a fresh setup, the semantic cache hit and cross-session memory retrieval may not register on the first pass — the indexes need a few writes before they're queryable. Run the flow a couple of times to warm them and both fire reliably.

---

## Architecture

```
User Query
    ↓
LangGraph Agent (orchestration)
    ↓
┌─────────────────────────────────────────────────────────────┐
│ Redis Iris                                                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Agent Memory │  │  LangCache   │  │   Context    │       │
│  │              │  │              │  │  Retriever   │       │
│  │ • STM / LTM  │  │ • Check /    │  │ • Search /   │       │
│  │   retrieve   │  │   save       │  │   filter     │       │
│  │ • Store new  │  │   responses  │  │   data       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         ↑                                     ↑              │
│         │          ┌──────────────┐          │              │
│         └──────────│ RDI stand-in │──────────┘              │
│                    │ PostgreSQL → │                         │
│                    │    Redis     │                         │
│                    └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
    ↓
Personalized Response
```

**Data flow:**
1. User sends a query.
2. **Agent Memory** retrieves session history (STM) and stored preferences (LTM).
3. **LangCache** checks for a semantically similar cached response.
4. On a miss, **Context Retriever** fetches real data via auto-generated MCP tools.
5. The LLM generates a response using memory context and retrieved data.
6. **Agent Memory** stores the new turn and any extracted facts.
7. **LangCache** caches the response for future similar queries.

---

## Features

### 🧠 Agent Memory

Short-term memory holds conversation history within a session. Long-term memory extracts durable facts (preferences, constraints, personal details) and retrieves them across sessions via semantic search.

```
Session 1 → User: "I prefer luxury hotels with spa facilities"
          → Stored to LTM

Session 2 → User: "Recommend hotels in Barcelona"
          → LTM retrieved, response prioritizes luxury + spa
```

### ⚡ LangCache

Caches LLM responses by embedding and matches new queries semantically, not by exact string. A configurable similarity threshold trades correctness risk against hit rate.

```
"What are the best hotels in Paris?"  → miss, generated, cached
"Top places to stay in Paris?"        → hit, served from cache, no LLM call
```

Cache savings depend entirely on hit rate, which is a property of your traffic, not the product — a long tail of unique questions might sit at 10–20%, while a repetitive support workload could reach 80%. Measure your own before relying on a number.

### 🔧 Context Retriever

Point it at your Redis data, run auto-detect, and it generates a set of typed MCP tools — no API code. For this demo's five entities it produced **15 tools**: a `filter`, `get`, and `search` for each.

```
filter_hotel_by_destination_id   get_hotel_by_id   search_hotel_by_text
filter_activity_by_destination_id ...
```

Tool names follow an `operation_entity_by_field` pattern, so list the generated set and bind to what's actually there:

```python
tools = requests.post(mcp_url, json={"jsonrpc":"2.0","method":"tools/list","id":1},
                      headers=headers).json()["result"]["tools"]
```

Tools are generated *from* the entity model — there's no documented way to author or customize an individual tool, which is fine for this demo but something a real app may eventually need.

### 🔄 RDI (stand-in)

RDI uses change data capture to sync a source database into Redis continuously. It's still in preview and not generally available, so this repo stands in with `scripts/simulate_rdi.py`, which reads from PostgreSQL and writes JSON documents into Redis to produce the same end shape Context Retriever reads from. It is **not** a re-implementation of RDI's CDC — just enough to give the pipeline fresh data. Swap it for real RDI once you have access.

Sample data: hotels (8), destinations (8), activities (9), restaurants (9), plus a user-preferences table.

---

## Project Structure

```
.
├── backend/
│   ├── app.py                 # FastAPI server
│   ├── memory.py              # LangGraph agent with Iris integration
│   └── context_retriever.py   # MCP client for Context Retriever
├── frontend/                  # Web UI with live layer panels
├── database/
│   ├── schema.sql             # PostgreSQL schema
│   └── seed_data.sql          # Sample data
├── scripts/
│   ├── simulate_rdi.py        # RDI stand-in (PostgreSQL → Redis)
│   └── check_iris_services.py # Service health check
├── demo_flow.sh               # Full demo (colorful output)
├── demo_flow_simple.sh        # Simple demo (JSON output)
├── docker-compose.yml
├── .env.example
├── DEMO_SCRIPTS.md
├── TEST_FULL_DEMO.md
└── README.md
```

---

## Demo Flow

`./demo_flow.sh` runs the full sequence:

**Session 1** — set preferences (LTM extraction), first query (cache miss), similar query (semantic cache hit).
**Session 2** — cross-session memory retrieval, then a tool call returning real Barcelona hotels via Context Retriever.

`./demo_flow_simple.sh` runs the same flow with JSON-only output, useful for screenshots. See `DEMO_SCRIPTS.md` for details.

---

## Adapting to Your Domain

The Iris integration stays the same; only the data and intent detection change.

1. **Change the data** — update `database/schema.sql` and `database/seed_data.sql` for your domain.
2. **Update the Context Retriever Surface** — sync your data, create a Surface in Redis Cloud, run auto-detect, update `CONTEXT_RETRIEVER_AGENT_KEY`.
3. **Update intent detection** in `backend/context_retriever.py`.
4. **Update the system prompt** in `backend/memory.py`.

---

## Configuration

**LLM provider** — OpenAI by default; set `OPENAI_API_BASE` for a local OpenAI-compatible model, or edit `backend/memory.py` for other providers.

**Cache sensitivity** — `LANGCACHE_DISTANCE_THRESHOLD` in `.env` (lower = looser matching, more hits, higher correctness risk).

**Response format** — adjust the system prompt in `backend/memory.py`.

---

## Troubleshooting

**Cache or memory not firing on a fresh setup** — indexes need a few writes before they're queryable. Send the same query 2–3 times; subsequent runs hit reliably.

**Tool calls return 0 results** — confirm the sync script ran, data exists in Redis, and the Context Retriever Surface is configured in Redis Cloud.

**STM shows "No short-term memory yet"** — normal for the first message in a session.

---

## Credits

**Built by:** Balaji Sivasubramanian ([@balajisiva](https://github.com/balajisiva))

**Based on:** Redis's [redis-agent-memory-with-langgraph-demo](https://github.com/redis-developer/redis-agent-memory-with-langgraph-demo), which provided the Agent Memory + LangGraph foundation. This repo extends it with LangCache, Context Retriever, a PostgreSQL data layer, an RDI stand-in, and a live-panel UI.

**Built with:** [LangGraph](https://langchain-ai.github.io/langgraph/), [Redis Iris](https://redis.io/iris/), [PostgreSQL](https://www.postgresql.org/), [FastAPI](https://fastapi.tiangolo.com/), and [Docker](https://www.docker.com/).

---

## Resources

- Redis Iris: [redis.io/iris](https://redis.io/iris/)
- Agent Memory: [redis.io/agent-memory](https://redis.io/agent-memory/)
- LangCache: [redis.io/langcache](https://redis.io/langcache/)
- Context Retriever: [redis.io/context-retriever](https://redis.io/context-retriever/)
- LangGraph: [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/)

---

## License

MIT — see [LICENSE](LICENSE).
