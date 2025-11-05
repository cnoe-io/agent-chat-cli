#!/usr/bin/env python3
"""Test sanitize_stream_text with actual partial_result content"""
import sys
sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

from agent_chat_cli.a2a_client import sanitize_stream_text

# Actual content from diagnostic output
actual_partial_result = '''The current version of ArgoCD is **v3.1.8+becb020**. Here are some additional details:

- **Build Date:** 2025-09-30T15:33:46Z
- **Git Commit:** becb020064fe9be5381bf6e5818ff8587ca8f377
- **Git Tree State:** clean
- **Go Version:** go1.24.6
- **Compiler:** gc
- **Platform:** linux/amd64
- **Kustomize Version:** v5.7.0 (2025-06-28T07:00:07Z)
- **Helm Version:** v3.18.4+gd80839c
- **Kubectl Version:** v0.33.1
- **Jsonnet Version:** v0.21.0{"status":"completed","message":"The current version of ArgoCD is **v3.1.8+becb020**. Here are some additional details:\\n\\n- **Build Date:** 2025-09-30T15:33:46Z\\n- **Git Commit:** becb020064fe9be5381bf6e5818ff8587ca8f377\\n- **Git Tree State:** clean\\n- **Go Version:** go1.24.6\\n- **Compiler:** gc\\n- **Platform:** linux/amd64\\n- **Kustomize Version:** v5.7.0 (2025-06-28T07:00:07Z)\\n- **Helm Version:** v3.18.4+gd80839c\\n- **Kubectl Version:** v0.33.1\\n- **Jsonnet Version:** v0.21.0"}'''

print("=" * 100)
print("Testing sanitize_stream_text with actual partial_result content")
print("=" * 100)
print(f"\nInput length: {len(actual_partial_result)} chars")
print(f"Input first 100 chars: {actual_partial_result[:100]}")
print(f"Input last 100 chars: {actual_partial_result[-100:]}")
print("\n" + "-" * 100)

result = sanitize_stream_text(actual_partial_result)

print(f"\nOutput length: {len(result)} chars")
print(f"\nOutput:\n{result}")
print("\n" + "=" * 100)

# Check if result is just "Here"
if result.strip() == "Here":
    print("❌ BUG CONFIRMED: sanitize_stream_text returned only 'Here'!")
elif len(result) < 100:
    print(f"⚠️  WARNING: Output is very short ({len(result)} chars)")
else:
    print(f"✅ Output looks reasonable ({len(result)} chars)")
print("=" * 100)

