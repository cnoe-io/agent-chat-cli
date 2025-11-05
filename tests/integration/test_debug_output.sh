#!/bin/bash
# Simple test to capture debug output

cd /Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli

echo "Cleaning Python cache..."
rm -rf agent_chat_cli/__pycache__
find . -name "*.pyc" -delete

echo "Activating venv..."
source .venv/bin/activate

echo ""
echo "Running CLI with debug output capture..."
echo "show argocd version" | python -m agent_chat_cli a2a --token "foo" 2>&1 | tee /tmp/cli_output.txt

echo ""
echo "=========================================="
echo "Searching for DEBUG output..."
echo "=========================================="
grep "🔍 DEBUG:" /tmp/cli_output.txt || echo "❌ No DEBUG output found!"

echo ""
echo "=========================================="
echo "Checking for partial_result processing..."
echo "=========================================="
grep -i "partial_result" /tmp/cli_output.txt | head -5 || echo "❌ No partial_result mentions found!"

echo ""
echo "=========================================="
echo "Final response content..."
echo "=========================================="
grep -A 5 "Ai platform engineer Response" /tmp/cli_output.txt | tail -10

