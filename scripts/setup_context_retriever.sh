#!/bin/bash
# Setup script for Redis Context Retriever

set -e

echo "============================================================"
echo "Redis Context Retriever Setup"
echo "============================================================"

# Load environment variables
source .env

echo ""
echo "Step 1: Authenticate with Context Retriever"
echo "------------------------------------------------------------"
echo "Please run the following command and enter your email:"
echo ""
echo "  ctxctl auth login --username \"your-email@example.com\""
echo ""
read -p "Press Enter after you've authenticated..."

echo ""
echo "Step 2: Creating Context Retriever Surface"
echo "------------------------------------------------------------"
echo "This will create a surface named 'Travel Data' with your Redis connection..."
echo ""

# Create the surface
SURFACE_OUTPUT=$(ctxctl surface create \
  --name "Travel Data" \
  --models ./context-retriever/models.py \
  --redis-addr "${REDIS_HOST}:${REDIS_PORT}" \
  --redis-password "${REDIS_PASSWORD}")

echo "$SURFACE_OUTPUT"

# Extract surface ID (this is approximate - adjust based on actual output format)
SURFACE_ID=$(echo "$SURFACE_OUTPUT" | grep -o 'surface-[a-f0-9-]*' | head -1)

if [ -z "$SURFACE_ID" ]; then
  echo ""
  echo "⚠️  Could not automatically extract Surface ID."
  echo "Please find it in the output above and run:"
  echo ""
  echo "  export SURFACE_ID=<your-surface-id>"
  echo "  ctxctl agent create --surface-id \$SURFACE_ID --name \"Travel Agent\""
  echo ""
  exit 0
fi

echo ""
echo "✓ Surface created: $SURFACE_ID"

echo ""
echo "Step 3: Creating Agent Key"
echo "------------------------------------------------------------"

AGENT_OUTPUT=$(ctxctl agent create \
  --surface-id "$SURFACE_ID" \
  --name "Travel Agent")

echo "$AGENT_OUTPUT"

# Extract agent key
AGENT_KEY=$(echo "$AGENT_OUTPUT" | grep -o 'agent-[a-f0-9-]*' | head -1)

if [ -z "$AGENT_KEY" ]; then
  echo ""
  echo "⚠️  Could not automatically extract Agent Key."
  echo "Please find it in the output above."
  exit 0
fi

echo ""
echo "✓ Agent key created: $AGENT_KEY"

echo ""
echo "Step 4: Listing Available Tools"
echo "------------------------------------------------------------"

ctxctl tools list --agent-key "$AGENT_KEY"

echo ""
echo "============================================================"
echo "✓ Context Retriever Setup Complete!"
echo "============================================================"
echo ""
echo "Surface ID: $SURFACE_ID"
echo "Agent Key:  $AGENT_KEY"
echo ""
echo "Add these to your .env file:"
echo ""
echo "CONTEXT_RETRIEVER_SURFACE_ID=$SURFACE_ID"
echo "CONTEXT_RETRIEVER_AGENT_KEY=$AGENT_KEY"
echo ""
echo "Test a query:"
echo "  ctxctl tools call search_destination_by_text \\"
echo "    --agent-key \"$AGENT_KEY\" \\"
echo "    --query \"beach\""
echo ""
echo "============================================================"
