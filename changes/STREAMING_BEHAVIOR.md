# Streaming Behavior and Output Replacement

## Overview

The CLI now intelligently handles streaming responses and replaces streamed output with clean structured panels when appropriate.

## Behavior

### For JSON Structured Responses

When the agent returns a JSON response with metadata:

1. **Streaming Phase**:
   - Detects JSON responses early (if text starts with `{`)
   - Suppresses real-time printing to avoid showing raw JSON
   - Spinner continues showing "Waiting for agent..."

2. **Replacement Phase**:
   - After streaming completes, calculates how many terminal lines were used
   - Uses ANSI escape codes to move cursor up and clear those lines
   - Displays only the clean structured panel with the content

3. **Result**:
   - User sees smooth transition from spinner to panel
   - No duplicate or raw JSON output
   - Clean, professional presentation

**Example**:
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

1. **Streaming Phase**:
   - Text streams in real-time as it arrives
   - User sees immediate feedback character-by-character

2. **Completion Phase**:
   - Streaming text remains visible
   - Panel is added below with formatted version
   - Provides both streaming experience and final formatted presentation

**Example**:
```
🧑‍💻 You: help me debug
⏳ Waiting for agent... →
Here are the steps to debug your application:
1. Check logs
2. Review recent changes
3. Test in isolation

╭───────────── AI Platform Engineer Response ─────────────╮
│                                                         │
│  Here are the steps to debug your application:          │
│                                                         │
│  1. Check logs                                          │
│  2. Review recent changes                               │
│  3. Test in isolation                                   │
│                                                         │
╰─────────────────────────────────────────────────────────╯
```

## Technical Implementation

### Line Clearing Logic

```python
# Track what was actually printed
printed_text = ""

# During streaming
if not suppress_streaming:
    print(text, end="", flush=True)
    printed_text += text

# After streaming completes
if printed_text:
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

### ANSI Escape Codes Used

- `\033[F` - Move cursor up one line
- `\033[K` - Clear from cursor to end of line

These codes work in most modern terminals (Linux, macOS, Windows Terminal, WSL).

## Benefits

### User Experience
1. **No duplicate output** - Content appears only once in final form
2. **No raw JSON** - Structured data is always formatted nicely
3. **Clean presentation** - Professional, polished appearance
4. **Smooth transitions** - Spinner → Panel (no jarring jumps)

### Developer Experience
1. **Automatic detection** - No special flags or configuration needed
2. **Backward compatible** - Non-JSON responses work as before
3. **Terminal-aware** - Accounts for line wrapping based on width
4. **Robust** - Handles edge cases (narrow terminals, long lines)

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

## Compatibility

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

## Configuration

Currently no configuration options - behavior is automatic based on response type.

Future enhancements could include:
- Environment variable to disable line clearing
- Force streaming/panel-only modes
- Customize clearing behavior per terminal type




