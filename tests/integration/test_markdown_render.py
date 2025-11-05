#!/usr/bin/env python3
"""Test if Markdown rendering works correctly with our content"""
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()

test_content = """Here is the current ArgoCD version information:

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

If you need further details or assistance, feel free to ask!"""

print(f"Content length: {len(test_content)} chars")
print(f"First line: {test_content.split(chr(10))[0]}")
print()

console.print(Panel(
    Markdown(test_content),
    title="🤖 AI Platform Engineer Response",
    border_style="green",
    padding=(1, 2),
))

