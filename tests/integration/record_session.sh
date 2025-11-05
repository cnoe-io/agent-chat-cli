#!/bin/bash
# Record a terminal session showing the streaming behavior

echo "This script will record your CLI session"
echo "Press Ctrl+D when done recording"
echo ""
echo "Starting recording in 3 seconds..."
sleep 3

# Use script command to record terminal session
OUTPUT_FILE="/tmp/cli_session_$(date +%Y%m%d_%H%M%S).txt"

echo "Recording to: $OUTPUT_FILE"
echo "Commands to run:"
echo "  1. cd /Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli"
echo "  2. source .venv/bin/activate"
echo "  3. python -m agent_chat_cli"
echo "  4. Type: show argocd version"
echo "  5. Press Ctrl+C to exit CLI"
echo "  6. Press Ctrl+D to stop recording"
echo ""

# Record the session
script -q "$OUTPUT_FILE"

echo ""
echo "Recording saved to: $OUTPUT_FILE"
echo "You can view it with: cat $OUTPUT_FILE"

