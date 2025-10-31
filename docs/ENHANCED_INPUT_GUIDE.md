# Enhanced CLI Input Guide

## Overview

The enhanced input module provides better UX for collecting user input with styled prompts, validation, and smart field detection.

## Comparison: Basic vs Enhanced

### 1. Dropdown Selection

#### Before (Basic):
```
input_fields: [{"field_name": "environment", "field_values": ["dev", "staging", "prod"]}]

📝 Please select environment
environment: 
```
User has to type exact value or guess format.

#### After (Enhanced):
```
╭─────────────────────────────────────────────────────╮
│ 📝 Environment                                      │
│                                                     │
│ Please select the deployment environment           │
╰─────────────────────────────────────────────────────╯

Option    Value
────────────────────
[1]       dev
[2]       staging
[3]       prod

Enter number or value (or 'cancel' to skip)
Environment: 2
✓ Selected: staging
```

**Features:**
- ✅ Numbered options for easy selection
- ✅ Fuzzy matching (typing "stag" matches "staging")
- ✅ Visual confirmation of selection
- ✅ Cancel support
- ✅ Validation with helpful error messages

### 2. Multi-line Text Input

#### Before (Basic):
```
description: This is a single line input
```
No way to enter multiple lines.

#### After (Enhanced):
```
╭─────────────────────────────────────────────────────╮
│ 📝 Description                                      │
│                                                     │
│ Please provide a detailed description of the issue │
╰─────────────────────────────────────────────────────╯

┌─────────────────────────────────────────────────────┐
│ Enter your text below. Press Ctrl+D (Unix) or      │
│ Ctrl+Z + Enter (Windows) when done.                │
└─────────────────────────────────────────────────────┘

Line 1: The service crashed at 3pm
Line 2: Error logs show OOM exception
Line 3: Affects production environment
[Ctrl+D]

✓ Captured 3 lines (94 characters)
```

**Features:**
- ✅ Multi-line input with clear instructions
- ✅ Line and character count
- ✅ Proper EOF handling

### 3. Yes/No Confirmation

#### Before (Basic):
```
confirm: yes
```
User has to type "yes", "y", "true", etc.

#### After (Enhanced):
```
╭─────────────────────────────────────────────────────╮
│ 📝 Confirm                                          │
│                                                     │
│ Are you sure you want to delete this resource?     │
╰─────────────────────────────────────────────────────╯

Are you sure you want to delete this resource? (y/N): y
✓ Yes
```

**Features:**
- ✅ Clear y/N prompt with default
- ✅ Visual confirmation
- ✅ Returns "true"/"false" strings

### 4. Numeric Input with Validation

#### Before (Basic):
```
timeout: abc  ← No validation!
```

#### After (Enhanced):
```
╭─────────────────────────────────────────────────────╮
│ 📝 Timeout                                          │
│                                                     │
│ Connection timeout in seconds                       │
╰─────────────────────────────────────────────────────╯

Timeout (min: 1, max: 300): abc
❌ Please enter a valid integer
Timeout (min: 1, max: 300): 500
❌ Value must be at most 300
Timeout (min: 1, max: 300): 30
✓ Entered: 30
```

**Features:**
- ✅ Type validation (integers only)
- ✅ Range validation with helpful messages
- ✅ Clear min/max indicators

### 5. Multi-Field Forms

#### Before (Basic):
```
field1: value1
field2: value2
field3: value3
```
No context, no progress indication.

#### After (Enhanced):
```
╭─────────────────────────────────────────────────────╮
│ 📋 Form Input                                       │
│                                                     │
│ Please provide the following information:          │
╰─────────────────────────────────────────────────────╯

Field 1 of 3
╭─────────────────────────────────────────────────────╮
│ 📝 Repository Name                                  │
│                                                     │
│ GitHub repository (format: owner/repo)              │
╰─────────────────────────────────────────────────────╯

Repository Name: myorg/myrepo
✓ Entered: myorg/myrepo

Field 2 of 3
╭─────────────────────────────────────────────────────╮
│ 📝 Issue Title                                      │
│                                                     │
│ Brief summary of the issue                          │
╰─────────────────────────────────────────────────────╯

Issue Title: Fix critical bug in auth
✓ Entered: Fix critical bug in auth

Field 3 of 3
╭─────────────────────────────────────────────────────╮
│ 📝 Labels                                           │
│                                                     │
│ Comma-separated labels                              │
╰─────────────────────────────────────────────────────╯

Option    Value
────────────────────
[1]       bug
[2]       enhancement
[3]       documentation

Labels: 1
✓ Selected: bug

╭──────────────── Summary ────────────────────╮
│ ✓ Form completed                            │
│                                             │
│   • repository_name: myorg/myrepo           │
│   • issue_title: Fix critical bug in auth  │
│   • labels: bug                             │
╰─────────────────────────────────────────────╯
```

**Features:**
- ✅ Progress indicator (Field X of Y)
- ✅ Per-field descriptions in styled panels
- ✅ Final summary of all inputs
- ✅ Option to cancel with confirmation

## Integration with chat_interface.py

### Update render_answer() function:

```python
from agent_chat_cli.enhanced_input import (
    show_input_field,
    show_multi_field_form
)

def render_answer(answer: str, agent_name: str = "Agent"):
    structured = parse_structured_response(answer)
    
    if structured:
        content = structured.get('content', '').strip()
        metadata = structured.get('metadata')
        require_user_input = structured.get('require_user_input', False)
        
        # Display content
        if content:
            console.print("\n")
            console.print(Panel(
                Markdown(content),
                title=f"[agent]{agent_name} Response[/agent]",
                border_style="agent",
                padding=(1, 2)
            ))
        
        # Enhanced input handling
        if metadata and require_user_input:
            input_fields = metadata.get('input_fields', [])
            if input_fields:
                # Use enhanced multi-field form
                results = show_multi_field_form(input_fields)
                
                if results:
                    # Return results for automatic follow-up
                    return format_results_for_agent(results)
                else:
                    console.print("[yellow]⚠️  Form cancelled[/yellow]")
                    return None
        
        console.print("\n")
        return None
```

## Smart Field Detection

The enhanced input module automatically detects field types:

| Field Name Pattern | Input Type | Example |
|--------------------|------------|---------|
| `description`, `body`, `content`, `message`, `details` | Multi-line text | Issue description |
| `confirm`, `approved`, `enabled`, `active` | Yes/No | Confirmation prompts |
| `count`, `number`, `quantity`, `limit`, `timeout` | Numeric | Timeouts, limits |
| Has `field_values` | Dropdown | Environment selection |
| Default | Single-line text | Names, URLs, etc. |

## Validation Support

### Built-in Validators:

```python
from agent_chat_cli.enhanced_input import show_validated_input

# Email validation
email = show_validated_input("email", "email")
# Output: "Please enter a valid email address" if invalid

# URL validation
url = show_validated_input("website", "url")
# Output: "Please enter a valid URL (http:// or https://)" if invalid
```

### Custom Validation:

```python
def validate_github_repo(value: str) -> bool:
    """Validate GitHub repo format (owner/repo)"""
    return '/' in value and len(value.split('/')) == 2

# Use in your code
while True:
    repo = show_text_input("repository")
    if validate_github_repo(repo):
        break
    console.print("[red]❌ Invalid format. Use: owner/repo[/red]")
```

## Advanced Features

### 1. Conditional Fields

```python
def show_conditional_fields(base_field: Dict, dependent_fields: List[Dict]):
    """Show fields that depend on previous selections"""
    base_value = show_input_field(base_field)
    
    if base_value == "custom":
        # Show additional fields only if "custom" selected
        return show_multi_field_form(dependent_fields)
    
    return {base_field['field_name']: base_value}
```

### 2. Field Dependencies

```python
# Example: If user selects "Jira", ask for project key
# If user selects "GitHub", ask for repository
agent_choice = show_input_field({
    "field_name": "platform",
    "field_description": "Select platform",
    "field_values": ["Jira", "GitHub"]
})

if agent_choice == "Jira":
    project = show_input_field({
        "field_name": "project_key",
        "field_description": "Jira project key (e.g., CAIPE)"
    })
elif agent_choice == "GitHub":
    repo = show_input_field({
        "field_name": "repository",
        "field_description": "GitHub repository (e.g., org/repo)"
    })
```

### 3. Input History

```python
# Store recent inputs for auto-suggestions
input_history = {
    "repository": ["myorg/repo1", "myorg/repo2"],
    "project_key": ["CAIPE", "DEVOPS"]
}

def show_text_input_with_history(field_name: str, history: List[str]):
    """Show recent values as suggestions"""
    if history:
        console.print("[dim]Recent values:[/dim]")
        for val in history[-3:]:  # Show last 3
            console.print(f"  [dim]• {val}[/dim]")
    
    return show_text_input(field_name)
```

## Benefits

| Feature | Basic Input | Enhanced Input |
|---------|-------------|----------------|
| **Visual Appeal** | Plain text | Styled panels, colors, icons |
| **Validation** | None | Type checking, range validation |
| **User Guidance** | Minimal | Context, examples, hints |
| **Error Messages** | Generic | Specific, actionable |
| **Selection** | Type exact value | Number or fuzzy match |
| **Multi-line** | Not supported | Full support with EOF |
| **Progress** | None | Field X of Y |
| **Confirmation** | Text parsing | Visual Yes/No |
| **Cancellation** | Ctrl+C crash | Graceful with confirmation |
| **Summary** | None | Complete review before submit |

## Migration Path

### Phase 1: Drop-in Replacement
Replace basic `input()` calls with `show_input_field()`:

```python
# Before
value = input(f"{field_name}: ")

# After
value = show_input_field(field)
```

### Phase 2: Use Smart Detection
Let the module auto-detect field types:

```python
# Automatically uses:
# - Dropdown for field_values
# - Multi-line for "description"
# - Yes/No for "confirm"
# - Numeric for "timeout"
value = show_input_field(field)
```

### Phase 3: Full Forms
Use multi-field forms for complex inputs:

```python
results = show_multi_field_form(input_fields)
```

## Future Enhancements

1. **Auto-completion** - TAB to auto-complete from history
2. **Search in dropdown** - Type to filter large option lists
3. **Conditional visibility** - Show/hide fields based on previous answers
4. **Rich text editing** - Syntax highlighting for code snippets
5. **File upload** - Browse and select files
6. **Date/time picker** - Calendar interface for dates
7. **Progress bars** - Visual feedback for long operations

## Example: Complete Flow

```
User: "Create a GitHub issue"
Agent: [asks clarification - GitHub selected]

╭────────────────────────────────────────────────────────────╮
│ 📋 Form Input                                              │
│                                                            │
│ Please provide the following information:                 │
╰────────────────────────────────────────────────────────────╯

Field 1 of 4
╭────────────────────────────────────────────────────────────╮
│ 📝 Repository                                              │
│                                                            │
│ GitHub repository name (format: owner/repo)                │
╰────────────────────────────────────────────────────────────╯

Repository: myorg/myrepo
✓ Entered: myorg/myrepo

Field 2 of 4
╭────────────────────────────────────────────────────────────╮
│ 📝 Title                                                   │
│                                                            │
│ Brief summary of the issue                                 │
╰────────────────────────────────────────────────────────────╯

Title: Fix authentication bug
✓ Entered: Fix authentication bug

Field 3 of 4
╭────────────────────────────────────────────────────────────╮
│ 📝 Description                                             │
│                                                            │
│ Detailed description of the issue                          │
╰────────────────────────────────────────────────────────────╯

┌──────────────────────────────────────────────────────────┐
│ Enter your text below. Press Ctrl+D when done.          │
└──────────────────────────────────────────────────────────┘

Line 1: Users are unable to log in
Line 2: Error occurs on password submission
Line 3: Affects all users since last deploy
[Ctrl+D]

✓ Captured 3 lines (112 characters)

Field 4 of 4
╭────────────────────────────────────────────────────────────╮
│ 📝 Labels                                                  │
│                                                            │
│ Issue labels (select one or more)                          │
╰────────────────────────────────────────────────────────────╯

Option    Value
────────────────────────
[1]       bug
[2]       critical
[3]       security
[4]       enhancement

Labels: 1
✓ Selected: bug

╭────────────────────── Summary ──────────────────────────╮
│ ✓ Form completed                                        │
│                                                         │
│   • repository: myorg/myrepo                            │
│   • title: Fix authentication bug                      │
│   • description: Users are unable to log in...         │
│   • labels: bug                                         │
╰─────────────────────────────────────────────────────────╯

➡️  Sending form data to agent...

[Agent creates the issue]

✓ GitHub issue created: #123
🔗 https://github.com/myorg/myrepo/issues/123
```

Much better UX! 🎨

