# Redis Iris Platform Travel Agent Demo - Project State

**Last Updated:** 2026-05-25
**Status:** ✅ Fully Operational
**Repository:** https://github.com/balajisiva/redis-iris-travel-agent

## Current Working Configuration

### Redis Iris Platform Services

#### Agent Memory (LTM + STM)
- **Server URL:** https://gcp-us-east4.memory.redis.io
- **Store ID:** 56a20959bb0247d48edd6686d7ffe938
- **API Key:** mem1_5SyvtCUrNlf1MPi2Z1yWcf0TIs-gcVQNAL_AL3jPfDzLfNGcpPJjcSwaK1Br80Xx49FjkAFN_el9H_bOFuWbVajHhpt5CTNOx9p1ciSZUf3o3cYx_YTcj0vcYg7MYtTNTJUvwlvDhX5ueHC1Sg==
- **Status:** ✅ Working (fixed after tier upgrade)
- **Note:** Database connection is properly configured in Redis Cloud UI

#### LangCache (Semantic Caching)
- **Server URL:** https://aws-us-east-1.langcache.redis.io
- **Cache ID:** 5a3eb8280cbd466a99ceb7888d4a85f1
- **API Key:** lc1_0kYDdh7NkgBaOoGdXuShKHmQcwXbt35uh0K40nREh38EN6ulMwI0DV09iRlgt-PG4qrkV32t0Lp8LuX6M69r57n2fV8AFJMOiwhLgGwWeWQRCBBMdHJXXqvIHJXedpJz6u57qBRrYTFulay41A==
- **Distance Threshold:** 0.2
- **Status:** ✅ Working (99.65% semantic similarity matching achieved)

#### Context Retriever (MCP Tools)
- **Surface ID:** c4a6c188-d7b7-44a7-82bf-e31140215475
- **Agent Key:** cs_agent_AcSmwYjXt0Sngr_jEUAhVHV47sYRabj3AhjApWx1NPqH
- **Admin Key:** cs_admin_KaQdWkhx-VPnQFpWHWwws9tiPAKLzvWX4-3Y38y0lzE
- **Status:** ✅ Working (15 MCP tools auto-generated from Redis data)

### Backend Services

#### LLM Configuration
- **Provider:** OpenAI-compatible (local deployment)
- **Model:** openai/gpt-oss-120b
- **API Base:** http://100.73.53.47:8000/v1
- **API Key:** sk-local

#### Redis Cloud (Data Store)
- **Host:** snow-neosleek-wiselike-20623.db.redis.io
- **Port:** 10595
- **Password:** X82KxOYzZ7SM4eleZL4fzjQU3TRvAb7I
- **SSL:** false
- **Tier:** Upgraded (250 connections)

#### PostgreSQL (RDI Source)
- **Host:** 127.0.0.1
- **Port:** 5433
- **Database:** traveldb
- **User:** postgres
- **Status:** ✅ 36 records synced via RDI simulation

### Demo Configuration
- **Owner ID:** alice
- **Namespace:** langgraph-travel-demo
- **Agent ID:** travel-agent

## Recent Fixes Applied

### 1. Agent Memory LTM Fix (2026-05-25)
**Problem:** LTM returning 403/404 after Redis Cloud tier upgrade
**Root Cause:** Original store `6eb8ecb89a5e4e2aa9bc5cb9531f77ad` was deleted during upgrade
**Solution:** Created new store with database connection properly configured
**Result:** ✅ LTM search and write operations working

### 2. LangCache Fix (2026-05-25)
**Problem:** Cache returning 404 after tier upgrade
**Root Cause:** Original cache `4c2c9ad34c314d18a1a0aab907506f43` was deleted
**Solution:** Created new cache with ID `5a3eb8280cbd466a99ceb7888d4a85f1`
**Result:** ✅ Semantic caching achieving 99.65% similarity matches

### 3. Frontend LLM Output Rendering (2026-05-25)
**Problem:** LLM responses displayed as raw text with bullets, not scannable
**Approach:** Instead of constraining LLM with strict prompts, handle formatting in UI
**Changes:**
- Updated `backend/memory.py` system prompt to be natural and helpful
- Modified `frontend/app.js` to parse bullet points and render as HTML `<ul>` lists
- Added CSS in `frontend/styles.css` for clean list styling with separators
- Rebuilt frontend container to apply changes

**Commit:** acabbf1 - "Improve LLM output rendering with clean bullet list display"
**Result:** ✅ Clean, scannable bullet list display in UI

## Component Status

| Component | Status | Details |
|-----------|--------|---------|
| Agent Memory (STM) | ✅ Working | Session memory stored and retrieved |
| Agent Memory (LTM) | ✅ Working | Semantic search, write operations functional |
| LangCache | ✅ Working | 99.65% similarity matching, cost reduction |
| Context Retriever | ✅ Working | 15 MCP tools, real hotel/destination data |
| RDI Simulation | ✅ Working | 36 PostgreSQL records synced to Redis |
| Frontend UI | ✅ Working | Clean bullet list rendering |
| LangGraph Agent | ✅ Working | Tool orchestration, memory integration |

## Running the Demo

### Start Services
```bash
docker-compose up -d
```

### Access Points
- **Frontend UI:** http://localhost:8080
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### Rebuild Frontend (if needed)
```bash
docker-compose up -d --build frontend
```

### View Logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Architecture Overview

```
User Query → Frontend (React-like vanilla JS)
    ↓
Backend (FastAPI + LangGraph)
    ↓
LangCache Check (semantic similarity)
    ↓ (cache miss)
LangGraph Agent Node
    ↓
Context Retriever Node (MCP tools)
    ↓ (query intent analysis)
Tool Execution (search_hotels, search_destinations)
    ↓ (retrieves from Redis)
Redis Cloud (JSON documents from RDI)
    ↓
LLM Generation (with retrieved context)
    ↓
Agent Memory (LTM write + STM update)
    ↓
LangCache Store (for future queries)
    ↓
Frontend Render (parse bullets → HTML list)
```

## Key Learnings

1. **Redis Cloud Tier Upgrades:** Stores and caches can be deleted during upgrades, but data is preserved if database connections are properly configured
2. **LLM Prompt Engineering:** Fighting LLMs with overly strict prompts is less effective than handling output formatting in the UI layer
3. **Container Rebuilds:** Frontend containers need explicit `--build` flag to pick up JavaScript/CSS changes
4. **Semantic Caching:** Extremely effective with 99.65% similarity on related queries, significant cost reduction potential

## Important Files

- `.env` - All service credentials and configuration
- `backend/memory.py` - LangGraph agent with LLM integration
- `backend/context_retriever.py` - MCP tools from Redis data
- `frontend/app.js` - UI rendering with bullet list parsing
- `frontend/styles.css` - Clean list styling
- `docker-compose.yml` - Service orchestration

## Next Steps / Future Enhancements

- Consider adding user authentication
- Add more destination data to demonstrate RDI scalability
- Implement conversation history UI
- Add analytics dashboard for cache hit rates and memory usage
- Consider deploying to production environment

---

**Repository:** https://github.com/balajisiva/redis-iris-travel-agent
**Demo Owner:** alice
**Last Commit:** acabbf1 (Frontend rendering improvements)
