# Streaming Display Configuration Guide

**Status**: 🟢 In-use  
**Category**: Configuration & Setup  
**Date**: November 7, 2025

## Overview

The CLI supports configurable streaming behavior, allowing users to control whether to show real-time streaming text or suppress it and only show the final structured panel. This provides flexibility based on user preferences and use cases.

## Configuration Options

### Default Behavior

**Default: Streaming ON** (`true`)
- Shows text as it arrives in real-time
- Provides immediate feedback
- Best for long responses where you want to see progress
- Final panel still displayed for clean formatting

### Option 1: Command-Line Flags

Use the `--show-streaming` or `--no-show-streaming` flag:

```bash
# Show streaming text (default)
agent-chat-cli a2a --show-streaming

# Suppress streaming, only show final panel
agent-chat-cli a2a --no-show-streaming
```

### Option 2: Environment Variable

Set the `A2A_SHOW_STREAMING` environment variable:

```bash
# Enable streaming (default)
export A2A_SHOW_STREAMING=true
agent-chat-cli a2a

# Disable streaming
export A2A_SHOW_STREAMING=false
agent-chat-cli a2a

# Also accepts: 0/1, yes/no
export A2A_SHOW_STREAMING=0    # Disabled
export A2A_SHOW_STREAMING=no   # Disabled
export A2A_SHOW_STREAMING=1    # Enabled
export A2A_SHOW_STREAMING=yes  # Enabled
```

### Option 3: .env File

Create a `.env` file:

```bash
# .env file
A2A_SHOW_STREAMING=false
A2A_HOST=localhost
A2A_PORT=8000
```

Then load it:

```bash
export $(cat .env | xargs)
agent-chat-cli a2a
```

## Behavior Comparison

### With Streaming Enabled (Default)

```
🧑‍💻 You: explain kubernetes pods
⏳ Waiting for agent... →
Kubernetes Pods are the smallest deployable units in Kubernetes.
They represent a single instance of a running process in your cluster.
Each pod can contain one or more containers that share resources...

╭───────────── AI Platform Engineer Response ─────────────╮
│                                                         │
│  Kubernetes Pods are the smallest deployable units...   │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

**Pros:**
- ✅ Immediate feedback as text arrives
- ✅ Great for long responses
- ✅ Shows progress for multi-part answers
- ✅ More engaging user experience

**Cons:**
- ❌ Text may appear twice (streaming + panel, depending on clear mode)
- ❌ Less clean for short responses

### With Streaming Disabled

```
🧑‍💻 You: explain kubernetes pods
⏳ Waiting for agent... →

╭───────────── AI Platform Engineer Response ─────────────╮
│                                                         │
│  Kubernetes Pods are the smallest deployable units...   │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

**Pros:**
- ✅ Cleaner, more professional appearance
- ✅ Text appears only once
- ✅ Better for screenshots/demos

**Cons:**
- ❌ No visual feedback during response generation
- ❌ Less engaging for long responses

## Configuration Precedence

Settings are applied in this order (highest to lowest):

1. **Environment Variable** - `A2A_SHOW_STREAMING`
2. **Command-Line Flag** - `--show-streaming` / `--no-show-streaming`
3. **Default Value** - `true` (streaming enabled)

Example:
```bash
# Environment variable takes precedence
export A2A_SHOW_STREAMING=false
agent-chat-cli a2a --show-streaming  # Streaming is OFF (env var wins)

# Without environment variable, flag is used
unset A2A_SHOW_STREAMING
agent-chat-cli a2a --no-show-streaming  # Streaming is OFF (flag used)

# No env var or flag, uses default
agent-chat-cli a2a  # Streaming is ON (default)
```

## Use Cases

### When to Enable Streaming

Enable streaming when:
- Working interactively with long responses
- Debugging or developing agents
- You want to see the agent's "thought process"
- Network is slow and you want progress feedback
- Responses typically contain multiple paragraphs

### When to Disable Streaming

Disable streaming when:
- Creating demos or screenshots
- Responses are typically short
- You prefer minimal, clean output
- Recording terminal sessions
- Using screen readers or accessibility tools
- Terminal doesn't support line clearing well

## Special Cases

### JSON Structured Responses

For JSON responses with metadata (like interactive input prompts), streaming is **automatically suppressed** regardless of the flag setting. This ensures clean display of structured content.

**Always displays as:**
```
⏳ Waiting for agent... →

╭───────────── AI Platform Engineer Response ─────────────╮
│  Select an action...                                    │
╰─────────────────────────────────────────────────────────╯

📝 Would you like to...
```

No raw JSON is ever shown, regardless of streaming setting.

## Terminal Compatibility

The streaming feature uses ANSI escape codes for line clearing. Works with:

- ✅ Modern Linux terminals (GNOME Terminal, Konsole, etc.)
- ✅ macOS Terminal and iTerm2
- ✅ Windows Terminal and WSL
- ✅ VS Code integrated terminal
- ✅ tmux and screen (with proper TERM settings)

May not work perfectly with:
- ❌ Very old terminals without ANSI support
- ❌ Some terminal emulators with limited escape code support
- ❌ Certain screen reader configurations

In case of compatibility issues, simply disable streaming with `--no-show-streaming`.

## Examples

### Production Deployment

For production environments, you might want clean output:

```bash
# In your deployment script
export A2A_SHOW_STREAMING=false
export A2A_HOST=agent.example.com
export A2A_PORT=443
export A2A_TLS=true

agent-chat-cli a2a
```

### Development/Testing

For interactive development, keep streaming enabled:

```bash
# Quick testing with streaming
agent-chat-cli a2a --host localhost --port 8000 --show-streaming
```

### CI/CD Pipeline

In automated pipelines, disable streaming for cleaner logs:

```bash
#!/bin/bash
export A2A_SHOW_STREAMING=false
echo "test query" | agent-chat-cli a2a --host test-agent --port 8000
```

## Troubleshooting

### Issue: Streaming text looks garbled

**Solution:** Terminal may not support ANSI codes properly.
```bash
agent-chat-cli a2a --no-show-streaming
```

### Issue: Text appears twice even with streaming off

**Possible Cause:** Environment variable is set to `true`.
```bash
# Check current setting
echo $A2A_SHOW_STREAMING

# Unset or override
unset A2A_SHOW_STREAMING
agent-chat-cli a2a --no-show-streaming
```

### Issue: No visual feedback during long responses

**Expected:** When streaming is disabled, only the spinner shows progress.

**Solution:** If you want feedback, enable streaming:
```bash
agent-chat-cli a2a --show-streaming
```

## Summary

| Setting | Command | Result |
|---------|---------|--------|
| Default | `agent-chat-cli a2a` | Streaming ON |
| Flag | `agent-chat-cli a2a --show-streaming` | Streaming ON |
| Flag | `agent-chat-cli a2a --no-show-streaming` | Streaming OFF |
| Env | `A2A_SHOW_STREAMING=false agent-chat-cli a2a` | Streaming OFF |
| Env | `A2A_SHOW_STREAMING=true agent-chat-cli a2a` | Streaming ON |

**Recommendation:** Keep the default (streaming ON) for interactive use, and disable for scripts, demos, or compatibility reasons.

---

**This provides flexible streaming configuration for any use case!** ⚙️

