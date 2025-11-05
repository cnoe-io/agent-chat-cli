#!/usr/bin/env python3
"""Test sanitize_stream_text function with actual data"""
import sys
sys.path.insert(0, '/Users/sraradhy/cisco/eti/sre/cnoe/agent-chat-cli')

from agent_chat_cli.a2a_client import sanitize_stream_text

# Sample text from user's terminal output (reconstructed)
sample_text = '''Here is the current ArgoCD version information:

- **Version**: v3.1.8+becb020
- **Build Date**: 2025-09-30T15:33:46Z
- **Git Commit**: becb020064fe9be5381bf6e5818ff8587ca8f377
- **Git Tree State**: clean
- **Go Version**: go1.24.6
- **Compiler**: gc
- **Platform**: linux/amd64
- **Kustomize Version**: v5.7.0 (2025-06-28T07:00:07Z)
- **Helm Version**: v3.18.4+gd80839c
- **Kubectl Version**: v0.33.1
- **Jsonnet Version**: v0.21.0

If you need further details or assistance, feel free to ask!{"status":"completed","message":"Here is the current ArgoCD version information:\\n\\n- **Version**: v3.1.8+becb020\\n- **Build Date**: 2025-09-30T15:33:46Z\\n- **Git Commit**: becb020064fe9be5381bf6e5818ff8587ca8f377\\n- **Git Tree State**: clean\\n- **Go Version**: go1.24.6\\n- **Compiler**: gc\\n- **Platform**: linux/amd64\\n- **Kustomize Version**: v5.7.0 (2025-06-28T07:00:07Z)\\n- **Helm Version**: v3.18.4+gd80839c\\n- **Kubectl Version**: v0.33.1\\n- **Jsonnet Version**: v0.21.0\\n\\nIf you need further details or assistance, feel free to ask!"}'''

print("=" * 100)
print("Testing sanitize_stream_text")
print("=" * 100)
print(f"\nInput length: {len(sample_text)} chars")
print(f"\nInput (first 200 chars):\n{sample_text[:200]}")
print("\n" + "-" * 100)

result = sanitize_stream_text(sample_text)

print(f"\nOutput length: {len(result)} chars")
print(f"\nOutput:\n{result}")
print("\n" + "=" * 100)

