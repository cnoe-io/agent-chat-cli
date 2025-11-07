# Dynamic Form Support for Structured User Input

**Status**: 🟢 In-use
**Category**: Features & Enhancements
**Date**: November 7, 2025

## Overview

Agent-Chat-CLI now supports **structured metadata responses** with **dynamic form generation**, providing an interactive CLI experience for complex user inputs. Instead of manually typing JSON, users are guided through beautiful interactive prompts with validation.

## The Problem

Previously, when agents needed structured input (e.g., creating Jira tickets, deploying applications), users had to:

1. **Manually format JSON** - error-prone and tedious
2. **Remember field names** - no autocomplete or guidance
3. **Handle validation client-side** - could submit invalid data
4. **Type everything at once** - no interactive field-by-field input

### Before (Manual Text Input)
```
🤖 Agent: To create a Jira ticket, I need:
- Project Key (choose from: CAIPE, DEVOPS, PLATFORM)
- Issue Type (Bug, Task, Story)
- Summary (brief description)

💬 You: ▊ (user types everything manually as JSON)
{"project_key": "CAIPE", "issue_type": "Bug", "summary": "Fix login"}
```

## The Solution

Dynamic forms provide an **interactive, validated, and beautiful** user experience:

### After (Interactive Forms) ✨
```
🤖 Agent: To create a Jira ticket, I need the following information:

┌─ 📋 Input Required ──────────────────┐
│                                      │
└──────────────────────────────────────┘

Project Key description here
Options: CAIPE, DEVOPS, PLATFORM
project_key: ▊ CAIPE

Issue Type description
Options: Bug, Task, Story, Epic
issue_type: ▊ Bug

Brief summary of the issue
summary: ▊ Fix login button

┌─ 📝 Your Input ────────────────┐
│ Field       │ Value            │
├─────────────┼──────────────────┤
│ project_key │ CAIPE            │
│ issue_type  │ Bug              │
│ summary     │ Fix login button │
└─────────────┴──────────────────┘

Submit this information? [Y/n]: ▊
```

## How It Works

### 1. Agent Sends Structured Metadata

Backend agent responds with:
```json
{
  "content": "To create a Jira ticket, I need the following information:",
  "require_user_input": true,
  "is_task_complete": false,
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "field_name": "project_key",
        "field_description": "GitHub repository (format: owner/repo)",
        "field_values": ["CAIPE", "DEVOPS", "PLATFORM"]
      },
      {
        "field_name": "summary",
        "field_description": "Brief summary of the issue",
        "field_values": null
      }
    ]
  }
}
```

### 2. CLI Parses and Renders Form

The client:
1. Parses the structured response using `parse_structured_response()`
2. Renders the main content (agent message)
3. Detects `require_user_input: true` and metadata
4. Calls `render_metadata_form()` to show interactive prompts

### 3. User Fills Form Interactively

Each field is prompted:
- **Choice fields**: Show options, validate selection
- **Text fields**: Free-form input
- **Descriptions**: Display field help text
- **Validation**: Re-prompt on invalid input

### 4. Client Submits to Agent

After confirmation, the form data is sent back as JSON:
```json
{
  "project_key": "CAIPE",
  "issue_type": "Bug",
  "summary": "Fix login authentication"
}
```

The agent receives this and continues execution.

## Implementation Details

### New Functions

#### `parse_structured_response(text: str) -> dict`
Parses structured JSON responses from agents with support for two formats:

1. **UserInputMetaData prefix format**: `UserInputMetaData: {...}`
2. **Legacy plain JSON**: `{...}`

```python
def parse_structured_response(text: str) -> dict:
    """
    Returns dict with: content, require_user_input, metadata
    Gracefully falls back to plain text if not JSON
    """
    # Check for UserInputMetaData: prefix
    if text.strip().startswith('UserInputMetaData:'):
        json_str = text.strip()[len('UserInputMetaData:'):].strip()
        data = json.loads(json_str)
        return {
            "content": data.get("content", text),
            "require_user_input": data.get("require_user_input", False),
            "metadata": data.get("metadata")
        }
    # Try plain JSON parsing
    # Fall back to plain text
```

**Location**: `agent_chat_cli/a2a_client.py` (lines 234-278)

#### `render_metadata_form(metadata: dict, console: Console) -> dict`
Renders an interactive CLI form using `rich` components:

- **Visual panel**: "📋 Input Required" header
- **Field-by-field prompts**: Interactive input with descriptions
- **Choice validation**: Re-prompt on invalid selections
- **Summary table**: Shows collected data before submission
- **Confirmation**: User can review and cancel

```python
def render_metadata_form(metadata: dict, console: Console) -> dict:
    """
    Returns dict of field_name -> user_value
    Returns {} if user cancels
    """
    input_fields = metadata.get("input_fields", [])
    
    for field in input_fields:
        if field.get("field_values"):
            # Choice field with validation
            value = Prompt.ask(field_name, default=...)
        else:
            # Text field
            value = Prompt.ask(field_name)
    
    # Show summary table
    # Confirm before submitting
```

**Location**: `agent_chat_cli/a2a_client.py` (lines 281-353)

### Integration Points

Both streaming and non-streaming modes follow the same pattern:

#### Streaming Mode (lines 1001-1027)
```python
# After streaming completes
if final_response_text:
    # Parse for structured metadata
    parsed = parse_structured_response(final_response_text)
    
    # Render main content
    render_answer(parsed["content"], agent_name=...)
    
    # Check if form is needed
    if parsed["require_user_input"] and parsed["metadata"]:
        form_data = render_metadata_form(parsed["metadata"])
        
        if form_data:
            # Send structured data back to agent
            await handle_user_input(json.dumps(form_data), token)
```

#### Non-Streaming Mode (lines 1052-1076)
Same pattern ensures consistency across both modes.

## Features

### Field Type Support
- ✅ **Text fields**: Free-form text input
- ✅ **Choice fields**: Validated selection from predefined options  
- ✅ **Descriptions**: Help text displayed for each field
- ✅ **Validation**: Automatic validation for choice fields with re-prompting

### User Experience
- ✅ **Interactive prompts**: Beautiful CLI forms using `rich.prompt`
- ✅ **Visual feedback**: Color-coded panels, fields, and descriptions
- ✅ **Input summary**: Table showing collected data before submission
- ✅ **Confirmation step**: Review and confirm or cancel
- ✅ **Error handling**: Re-prompts on invalid choices

### Integration
- ✅ **Automatic detection**: Parses JSON responses for metadata
- ✅ **Seamless flow**: Automatically sends form data back to agent
- ✅ **Universal support**: Works in both streaming and non-streaming modes
- ✅ **Backward compatible**: Gracefully handles non-metadata responses

## Benefits

### 1. Better UX
No more manual JSON typing - users are guided through interactive prompts field by field.

### 2. Input Validation
Choice fields are validated automatically. Invalid selections are rejected with clear error messages.

### 3. Consistency
Same structured format as agent-forge, ensuring consistent UX across all clients.

### 4. Error Reduction  
Users can't submit invalid data - validation happens before submission.

### 5. Discoverability
Field descriptions and available options are shown inline, no need to remember schemas.

## Implementation Files

### Modified Files

**1. `agent_chat_cli/a2a_client.py`**
- **Lines 234-278**: Added `parse_structured_response()` for JSON parsing
- **Lines 281-353**: Added `render_metadata_form()` for interactive forms
- **Lines 1001-1027**: Integrated into streaming mode
- **Lines 1052-1076**: Integrated into non-streaming mode
- **Imports**: Added `rich.prompt.Prompt`, `rich.prompt.Confirm`, `rich.table.Table`

### New Files

**1. `tests/test_user_input_metadata.py`**
- Unit tests for successful form rendering scenarios
- Tests choice validation
- Tests data collection and submission

**2. `tests/test_user_input_metadata_failure.py`**
- Tests for error handling and edge cases
- Tests cancellation flow
- Tests malformed metadata

**3. `examples/test_dynamic_form.py`**
- Example usage and demonstrations
- Sample form configurations

**4. `changes/DYNAMIC_FORMS.md`**
- This architecture decision record

**5. `uv.lock`**
- Updated dependencies (rich prompt features)

## Testing

### Manual Testing

Start the agent-chat-cli and test with queries that require structured input:

```bash
# Start agent-chat-cli
python -m agent_chat_cli

# Try a query that requires input
💬 You: create a jira ticket

# You should see:
# 1. Agent's response explaining what's needed
# 2. Interactive form with field prompts
# 3. Summary table
# 4. Confirmation prompt
# 5. Agent processes the submitted data
```

### Debug Mode

Enable debug logging to see parsing and form rendering:

```bash
# Enable debug mode
export A2A_DEBUG_CLIENT=true
python -m agent_chat_cli

# Look for log output:
🎨 Structured metadata detected - rendering form
📤 Sending form data back to agent: {"project_key": "CAIPE", ...}
```

### Automated Tests

Run the test suite:

```bash
# Run all tests
pytest tests/test_user_input_metadata.py
pytest tests/test_user_input_metadata_failure.py

# Run with coverage
pytest --cov=agent_chat_cli tests/
```

## Compatibility

### Backward Compatibility
- ✅ Works with agents that don't send metadata (no-op, continues as before)
- ✅ Gracefully handles plain text responses
- ✅ No breaking changes to existing functionality

### Agent Compatibility
- ✅ Works with any agent sending the structured JSON format
- ✅ No agent-side changes required if already using metadata format
- ✅ Compatible with both P2P and A2A protocols

### Client Compatibility
- ✅ Similar to agent-forge's dynamic forms
- ✅ Consistent UX across CLI and web clients
- ✅ Same metadata schema

## Future Enhancements

Potential improvements for future iterations:

1. **Additional field types**: Number, date, boolean, file upload
2. **Validation rules**: Regex patterns, min/max length, custom validators
3. **Multi-select fields**: Choose multiple options from a list
4. **Conditional fields**: Show/hide fields based on other field values
5. **Form history**: Auto-fill from previous submissions
6. **Field dependencies**: Required fields based on other selections

---

**This brings agent-chat-cli's capabilities on par with agent-forge for dynamic user interactions!** 🎉

