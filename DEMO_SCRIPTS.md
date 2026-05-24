# Demo Scripts for Blog

**Project:** AI Travel Agent powered by Redis Iris

Two scripts to demonstrate the complete integration:

## Quick Start

```bash
# Full demo with colorful output and explanations
./demo_flow.sh

# Simple demo with just JSON output
./demo_flow_simple.sh
```

---

## Script 1: `demo_flow.sh` (Full Demo)

**Perfect for:** Live demos, presentations, understanding the flow

**Features:**
- Colorful terminal output with section headers
- Detailed explanations of what each step demonstrates
- Shows all IRIS components working together
- Summary at the end

**What it demonstrates:**

### Session 1:
1. **Message 1:** User sets preferences → **LTM Extraction**
   - "My name is Sarah and I prefer luxury hotels with spa facilities near the beach. I'm vegetarian."
   - Shows extracted preferences stored in long-term memory

2. **Message 2:** Ask about destinations → **Cache Miss**
   - "What are the best luxury beach destinations in Europe?"
   - First time query, generates new response, saves to cache

3. **Message 3:** Ask similar question → **Semantic Cache Hit**
   - "Which European beach locations are ideal for a luxury vacation?"
   - Semantically similar query matches cache, saves LLM costs

### Session 2 (New Session):
4. **Message 1:** Ask for recommendations → **LTM Retrieval**
   - "Can you recommend destinations for me?"
   - Shows LTM persists across sessions (remembers preferences from Session 1)

5. **Message 2:** Ask for hotels → **Context Retriever Tool Calling**
   - "Find me luxury hotels in Barcelona"
   - Shows MCP tools retrieving real data from Redis

**Output Example:**
```
╔═══════════════════════════════════════════════════════════╗
║         REDIS IRIS PLATFORM - FULL DEMO FLOW             ║
║  Agent Memory • LangCache • Context Retriever • RDI      ║
╚═══════════════════════════════════════════════════════════╝

============================================================
SESSION 1 - MESSAGE 1: Setting User Preferences
============================================================

▶ User expresses preferences to be stored in Long-Term Memory...

User: "My name is Sarah and I always prefer luxury hotels..."

🧠 Long-Term Memory EXTRACTED (NEW):
  ✓ The user's name is Sarah.
  ✓ The user prefers luxury hotels with spa facilities near the beach.
  ✓ The user is vegetarian.
```

---

## Script 2: `demo_flow_simple.sh` (JSON Output)

**Perfect for:** Blog code blocks, screenshots, debugging

**Features:**
- Clean JSON output
- Easy to copy-paste results into blog
- Shows key data fields only
- No colors or formatting (terminal-agnostic)

**Output Example:**
```json
{
  "response": "Nice to meet you, Sarah! I've noted your preferences for luxury hotels with spa facilities near the beach...",
  "ltm_extracted": [
    "The user's name is Sarah.",
    "The user prefers luxury hotels with spa facilities near the beach.",
    "The user is vegetarian."
  ],
  "cache_hit": false
}
```

---

## Demo Flow Sequence

Both scripts follow this exact sequence:

```
┌─────────────────────────────────────────────────────────┐
│ SESSION 1: Building Context                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 1. Set Preferences (LTM Extraction)                     │
│    Input: "I prefer luxury hotels with spa..."          │
│    Output: LTM extracted ✓                              │
│                                                          │
│ 2. First Query (Cache Miss)                             │
│    Input: "Best luxury beach destinations in Europe?"   │
│    Output: Generated response, cached ✓                 │
│                                                          │
│ 3. Similar Query (Semantic Cache Hit)                   │
│    Input: "European beach locations for luxury?"        │
│    Output: Cache hit! Matched previous query ✓          │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ SESSION 2: Cross-Session Persistence                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 4. New Session - Test LTM Retrieval                     │
│    Input: "Recommend destinations for me?"              │
│    Output: Retrieved LTM from Session 1 ✓               │
│           (remembers: luxury, spa, beach, vegetarian)    │
│                                                          │
│ 5. Tool Calling - Context Retriever                     │
│    Input: "Find luxury hotels in Barcelona"             │
│    Output: MCP tool called, real data from Redis ✓      │
│           (Hotel Arts Barcelona - 4.7★ - luxury)         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## What Each Test Proves

### ✅ Agent Memory - Short-Term Memory (STM)
- **Session 1, Message 2+:** STM contains conversation history
- **Session 2:** Fresh STM (proves session isolation)

### ✅ Agent Memory - Long-Term Memory (LTM)
- **Extraction:** Preferences stored from natural language
- **Cross-Session Retrieval:** Session 2 retrieves facts from Session 1
- **Persistence:** LTM survives across sessions

### ✅ LangCache - Semantic Caching
- **Cache Miss:** First query generates new response
- **Semantic Hit:** Similar query (different words) matches cache
- **Cost Savings:** Cache hit avoids LLM call

### ✅ Context Retriever - MCP Tool Calling
- **Auto-Generated Tools:** search_hotel_by_text from Surface
- **Real Data:** Retrieves from Redis (synced via RDI)
- **LLM Integration:** Tool results used in response

### ✅ RDI - Data Synchronization
- **PostgreSQL → Redis:** 36 records synced
- **JSON Format:** Required by Context Retriever
- **Searchable:** RediSearch indexes enabled

---

## Expected Warnings (Non-Breaking)

You may see these warnings in the output - they're expected and don't break functionality:

### LangCache Index Warning
```
⚠ Cache index may still be recreating. Try again in a few seconds.
This is normal after Redis tier upgrade - index auto-recreates on writes.
```

**What it means:** Cache lookups fail initially, but saves work. Index auto-recreates.

### Agent Memory LTM Warning
```
⚠ LTM index may still be recreating after Redis upgrade.
```

**What it means:** LTM search returns empty initially. STM still works. Index auto-recreates on first write.

---

## Troubleshooting

### "No tool calls made"
```bash
# Check if backend is running
docker ps | grep backend

# Check backend logs
docker logs redis-agent-memory-with-langgraph-demo-backend-1 --tail 100

# Look for CONTEXT_RETRIEVER logs
docker logs redis-agent-memory-with-langgraph-demo-backend-1 | grep CONTEXT_RETRIEVER
```

### "Cache hit: false" on similar query
This is normal immediately after Redis tier upgrade. The LangCache index is recreating.

**Fix:** Run the script a few more times. After a few cache writes, the index will be ready and you'll see cache hits.

### "LTM retrieved: []" in Session 2
The Agent Memory LTM index is recreating after the Redis upgrade.

**Fix:**
1. Send a few more messages with preferences
2. Check logs: `docker logs redis-agent-memory-with-langgraph-demo-backend-1 --tail 50`
3. Look for successful LTM writes (no errors)
4. Rerun the script

---

## Blog Usage

### For Screenshots:
```bash
# Run simple version, capture clean JSON
./demo_flow_simple.sh > demo_output.txt
```

### For Live Demo:
```bash
# Run full version with colors
./demo_flow.sh
```

### For Copy-Paste Code Blocks:
Use the message strings from the scripts:

**Setting Preferences:**
```
My name is Sarah and I prefer luxury hotels with spa facilities near the beach. I'm also vegetarian.
```

**Cache Test Queries:**
```
# Query 1 (Cache Miss)
What are the best luxury beach destinations in Europe?

# Query 2 (Cache Hit - Semantic Match)
Which European beach locations are ideal for a luxury vacation?
```

**Cross-Session Test:**
```
Can you recommend destinations for me?
```

**Tool Calling Test:**
```
Find me luxury hotels in Barcelona
```

---

## Customizing the Demo

### Change the User Persona:
Edit `MESSAGE_1` in either script:
```bash
MESSAGE_1="My name is John and I prefer budget hostels in mountain locations. I'm vegan."
```

### Change the Queries:
Edit `MESSAGE_2`, `MESSAGE_3`, etc.:
```bash
MESSAGE_2="What are the best budget mountain destinations in Asia?"
MESSAGE_3="Which Asian mountain spots are good for budget travel?"
```

### Test Different Tools:
```bash
MESSAGE_5="Find activities in Tokyo"  # Triggers search_activity_by_text
MESSAGE_5="Recommend restaurants in Paris"  # Triggers search_restaurant_by_text
MESSAGE_5="Tell me about Lisbon"  # Triggers search_destination_by_text
```

---

## Success Criteria

After running either script, you should see:

- ✅ LTM extracted in Session 1, Message 1
- ✅ Cache miss in Session 1, Message 2
- ✅ Cache hit in Session 1, Message 3 (or after a few runs)
- ✅ LTM retrieved in Session 2, Message 1 (or after index recreates)
- ✅ Tool calls return 1-2 hotels in Session 2, Message 2
- ✅ STM shows conversation history from 2nd message onward
- ✅ No crashes or 500 errors

**All criteria met = Demo ready for blog! 🎉**
