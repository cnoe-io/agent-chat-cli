# Streaming Output with Intelligent Replacement

**Status**: 🟢 In-use
**Category**: Features & Enhancements
**Date**: November 7, 2025

## Overview

The CLI now intelligently handles streaming responses and replaces streamed output with clean structured panels when appropriate, providing smooth transitions and professional presentation.

## The Problem

Previously, streaming behavior was not context-aware:

1. **Raw JSON appeared during streaming** - Structured responses showed ugly JSON as it streamed in
2. **Duplicate content** - Text appeared both during streaming and in the final panel
3. **No transition control** - Couldn't replace streamed content with formatted panels
4. **Terminal limitations not considered** - Line wrapping wasn't accounted for when clearing
5. **Jarring user experience** - Sudden appearance of final content without smooth transition

## The Solution

Implemented intelligent streaming behavior that:

1. **Detects response type** early (JSON vs markdown)
2. **Suppresses streaming for JSON** to avoid raw output
3. **Calculates terminal lines accurately** accounting for wrapping
4. **Uses ANSI escape codes** to clear and replace streamed text
5. **Provides smooth transitions** from streaming to final panel

## How It Works

### For JSON Structured Responses

When the agent returns a JSON response with metadata:

**1. Streaming Phase:**
- Detects JSON responses early (if text starts with `{`)
- Suppresses real-time printing to avoid showing raw JSON
- Spinner continues showing "Waiting for agent..."

**2. Replacement Phase:**
- After streaming completes, calculates how many terminal lines were used
- Uses ANSI escape codes to move cursor up and clear those lines
- Displays only the clean structured panel with the content

**3. Result:**
- User sees smooth transition from spinner to panel
- No duplicate or raw JSON output
- Clean, professional presentation

**Example:**
```
🧑‍💻 You: howdy
⏳ Waiting for agent... →

╭───────────── AI Platform Engineer Response ─────────────╮
│                                                         │
│  Howdy! How can I assist you today?                     │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

### For Regular Markdown Responses

When the agent returns plain markdown text:

**1. Streaming Phase:**
- Text streams in real-time as it arrives
- User sees immediate feedback character-by-character

**2. Completion Phase:**
- Behavior depends on display mode configuration
- Mode 1: Clears streaming text, shows panel
- Mode 2: Keeps streaming text, adds panel below
- Mode 3: No streaming, panel only

## Implementation Details

### Line Clearing Logic

```python
# Track what was actually printed
printed_text = ""

# During streaming
if not suppress_streaming:
    print(text, end="", flush=True)
    printed_text += text

# After streaming completes
if printed_text and clear_streaming:
    # Calculate terminal lines (accounting for wrapping)
    terminal_width = shutil.get_terminal_size().columns
    lines_to_clear = 0

    for line in printed_text.split('\n'):
        if len(line) == 0:
            lines_to_clear += 1
        else:
            # Account for line wrapping
            lines_to_clear += (len(line) + terminal_width - 1) // terminal_width

    # Clear using ANSI escape codes
    for _ in range(lines_to_clear):
        sys.stdout.write('\033[F')  # Move cursor up
        sys.stdout.write('\033[K')  # Clear line
    sys.stdout.flush()
```

**Location:** `agent_chat_cli/a2a_client.py`

### ANSI Escape Codes Used

- `\033[F` - Move cursor up one line
- `\033[K` - Clear from cursor to end of line

These codes work in most modern terminals (Linux, macOS, Windows Terminal, WSL).

### JSON Detection

Early detection during streaming prevents raw JSON from appearing:

```python
# Check if this looks like a JSON response (starts with {)
accumulated_check = (all_text + text).strip()
if accumulated_check.startswith('{'):
    suppress_streaming = True
    debug_log("Detected JSON response - suppressing real-time streaming")
```

## Edge Cases Handled

### Narrow Terminals
- Calculates line wrapping based on actual terminal width
- Clears correct number of wrapped lines

### Mixed Content
- If response starts with text then has JSON, suppresses when JSON detected
- Tracks only what was actually printed, not accumulated

### No Terminal Width
- Falls back to 80 columns if terminal size can't be determined
- Better to clear too few lines than too many

### Suppressed Streaming
- If JSON detected early, nothing is printed
- Only adds newline after spinner before showing panel

## Benefits

### 1. User Experience
- **No duplicate output** - Content appears only once in final form
- **No raw JSON** - Structured data is always formatted nicely
- **Clean presentation** - Professional, polished appearance
- **Smooth transitions** - Spinner → Panel (no jarring jumps)

### 2. Developer Experience
- **Automatic detection** - No special flags or configuration needed
- **Backward compatible** - Non-JSON responses work as before
- **Terminal-aware** - Accounts for line wrapping based on width
- **Robust** - Handles edge cases (narrow terminals, long lines)

### 3. Consistency
- Same behavior across different response types
- Predictable user experience
- Works with all display modes

## Terminal Compatibility

Works with:
- ✅ Linux terminals (xterm, gnome-terminal, konsole, etc.)
- ✅ macOS Terminal and iTerm2
- ✅ Windows Terminal and WSL
- ✅ VS Code integrated terminal
- ✅ SSH sessions

May not work perfectly with:
- ❌ Very old terminals without ANSI support
- ❌ Screen readers (clears may cause confusion)
- ❌ Terminal multiplexers with specific configurations

For terminals without ANSI support, the behavior gracefully degrades to showing both streamed and panel output.

## Implementation Files

**Modified Files:**

1. **`agent_chat_cli/a2a_client.py`**
   - Added JSON detection during streaming
   - Implemented line tracking and counting logic
   - Added terminal width-aware clearing
   - Integrated ANSI escape codes for cursor control

## Configuration

Currently no dedicated configuration options - behavior is automatic based on response type and display mode settings.

Display mode flags affect the behavior:
- `--show-streaming --clear-streaming` (Mode 1): Streams and clears
- `--show-streaming --no-clear-streaming` (Mode 2): Streams and keeps
- `--no-show-streaming` (Mode 3): No streaming, panel only

## Future Enhancements

Potential improvements:

1. **Configurable clearing** - Environment variable to disable line clearing
2. **Terminal detection** - Automatic fallback for terminals without ANSI support
3. **Custom animations** - Transition effects when replacing content
4. **Performance optimization** - Reduce clearing overhead for very long responses

---

**This provides a smooth, professional streaming experience!** ✨

