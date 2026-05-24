#!/bin/bash

# Simplified Demo Flow - Just the queries and key results
# Perfect for blog screenshots and copy-paste

API_URL="http://localhost:8080/api/chat"

SESSION_1="demo-$(date +%s)"
SESSION_2="demo-$(date +%s)-2"

echo "============================================"
echo "AI Travel Agent - Quick Demo"
echo "Powered by Redis Iris Platform"
echo "============================================"
echo ""
echo "Session 1: $SESSION_1"
echo "Session 2: $SESSION_2"
echo ""

# Helper function
send() {
    curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$1\", \"session_id\": \"$2\"}"
}

echo "============================================"
echo "SESSION 1 - Message 1: Set Preferences"
echo "============================================"
echo "User: 'My name is Sarah and I prefer luxury hotels with spa facilities near the beach.'"
echo ""
send "My name is Sarah and I prefer luxury hotels with spa facilities near the beach. I'm also vegetarian." "$SESSION_1" | jq '{
    response: .assistant_message[:150],
    ltm_extracted: .extracted_long_term_memory,
    cache_hit: .cache_hit
}'
sleep 2

echo ""
echo "============================================"
echo "SESSION 1 - Message 2: First Query (Cache Miss)"
echo "============================================"
echo "User: 'What are the best luxury beach destinations in Europe?'"
echo ""
send "What are the best luxury beach destinations in Europe?" "$SESSION_1" | jq '{
    response: .assistant_message[:150],
    stm_count: (.short_term_memory | length),
    cache_hit: .cache_hit
}'
sleep 2

echo ""
echo "============================================"
echo "SESSION 1 - Message 3: Similar Query (Cache Hit Test)"
echo "============================================"
echo "User: 'Which European beach locations are ideal for a luxury vacation?'"
echo ""
send "Which European beach locations are ideal for a luxury vacation?" "$SESSION_1" | jq '{
    response: .assistant_message[:150],
    cache_hit: .cache_hit,
    matched_prompt: .matched_prompt,
    similarity_score: .similarity_score
}'
sleep 2

echo ""
echo "============================================"
echo "SESSION 2 - Message 1: Cross-Session LTM Test"
echo "============================================"
echo "User: 'Can you recommend destinations for me?'"
echo "(NEW SESSION - testing if LTM persists)"
echo ""
send "Can you recommend destinations for me?" "$SESSION_2" | jq '{
    response: .assistant_message[:200],
    ltm_retrieved: .long_term_memory,
    stm_count: (.short_term_memory | length)
}'
sleep 2

echo ""
echo "============================================"
echo "SESSION 2 - Message 2: Tool Calling Test"
echo "============================================"
echo "User: 'Find me luxury hotels in Barcelona'"
echo ""
send "Find me luxury hotels in Barcelona" "$SESSION_2" | jq '{
    response: .assistant_message[:200],
    tool_calls: [.tool_calls[] | {
        tool: .tool,
        params: .params,
        result_count: .result.count,
        results: [.result.results[]? | {name, rating, price_range}]
    }]
}'

echo ""
echo "============================================"
echo "Demo Complete! ✅"
echo "============================================"
echo ""
echo "Open http://localhost:8080 to see the UI"
echo "Check SESSION_1 ($SESSION_1) and SESSION_2 ($SESSION_2)"
