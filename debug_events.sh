#!/bin/bash

# Debug Events Script for Task Notifications
# This script runs the agent CLI with enhanced debug logging to capture task notification events

echo "🔍 Starting Agent CLI with Enhanced Debug Logging"
echo "📋 This will capture detailed event information including task notifications"
echo "💡 Look for events with 'calling', 'completed', or notification patterns"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Set debug flag and environment variables
export A2A_DEBUG_CLIENT=true
export A2A_HOST=localhost
export A2A_PORT=8000

echo "🚀 Starting CLI with debug enabled..."
echo "🔧 Agent: $A2A_HOST:$A2A_PORT"
echo "📝 Debug mode: ON"
echo "───────────────────────────────────────────"

# Use here-document to provide automatic input
python -m agent_chat_cli.a2a_client <<EOF
show argocd version
exit
EOF
