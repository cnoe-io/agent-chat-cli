# Agent Chat CLI Examples

## Interactive Input with Metadata

The CLI now supports structured responses with interactive input fields. When the agent returns a JSON response with metadata, the CLI automatically detects it and provides an interactive UI.

### Dropdown Selection

When the agent provides a list of options (`field_values`), the user sees a numbered list and can select by:
- Entering the number (e.g., `1`, `2`, `3`)
- Entering the exact value (e.g., `troubleshoot`)
- Entering a partial match (e.g., `trouble`)

**Example Response from Agent:**

```json
{
  "is_task_complete": false,
  "require_user_input": true,
  "content": "ArgoCD is not currently accessible—connection to localhost:8080 was refused. This usually means the ArgoCD server is not running or is unreachable.\n\nWould you like help diagnosing or starting the ArgoCD server?",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "field_name": "action",
        "field_description": "Would you like to troubleshoot, start the ArgoCD server, or specify a different ArgoCD API endpoint?",
        "field_values": [
          "troubleshoot",
          "start_server",
          "specify_endpoint"
        ]
      }
    ]
  }
}
```

**User Experience:**

```
╭──────────────── AI Platform Engineer Response ─────────────────╮
│                                                                │
│  ArgoCD is not currently accessible—connection to              │
│  localhost:8080 was refused. This usually means the ArgoCD     │
│  server is not running or is unreachable.                      │
│                                                                │
│  Would you like help diagnosing or starting the ArgoCD         │
│  server?                                                       │
│                                                                │
╰────────────────────────────────────────────────────────────────╯

📝 Would you like to troubleshoot, start the ArgoCD server, or specify a different ArgoCD API endpoint?

Select an option:

  [1]  troubleshoot
  [2]  start_server
  [3]  specify_endpoint

Enter your choice (number or value): 1

➡️  Sending: troubleshoot
```

### Text Input

When the agent requests open-ended input (no `field_values` or empty list), the user sees a text prompt.

**Example Response from Agent:**

```json
{
  "is_task_complete": false,
  "require_user_input": true,
  "content": "Please provide the endpoint URL for your ArgoCD server.",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "field_name": "endpoint_url",
        "field_description": "Enter the ArgoCD server endpoint URL",
        "field_values": []
      }
    ]
  }
}
```

**User Experience:**

```
╭──────────────── AI Platform Engineer Response ─────────────────╮
│                                                                │
│  Please provide the endpoint URL for your ArgoCD server.       │
│                                                                │
╰────────────────────────────────────────────────────────────────╯

📝 Enter the ArgoCD server endpoint URL

endpoint_url: https://argocd.example.com

➡️  Sending: https://argocd.example.com
```

### Multiple Input Fields

The CLI can handle multiple input fields in sequence:

```json
{
  "is_task_complete": false,
  "require_user_input": true,
  "content": "Let's configure your deployment.",
  "metadata": {
    "user_input": true,
    "input_fields": [
      {
        "field_name": "environment",
        "field_description": "Select the target environment",
        "field_values": ["development", "staging", "production"]
      },
      {
        "field_name": "namespace",
        "field_description": "Enter the Kubernetes namespace",
        "field_values": []
      }
    ]
  }
}
```

## Streaming with Structured Output

When streaming responses, the CLI:

1. **Shows streaming text** in real-time as it arrives
2. **Replaces with structured panel** after streaming completes
3. **Handles interactive input** if metadata requires it
4. **Automatically sends follow-up** with the user's selection

This provides immediate feedback while maintaining a clean, structured final presentation.

## Regular Markdown Responses

Non-structured responses continue to work as before, displayed in a beautiful markdown panel:

```markdown
Here's how to deploy your application:

1. First, ensure your cluster is ready
2. Apply the configuration: `kubectl apply -f config.yaml`
3. Verify the deployment: `kubectl get pods`
```

## Implementation Details

### For Agent Developers

To trigger interactive input, return a JSON response with this structure:

```json
{
  "is_task_complete": boolean,      // false if more interaction needed
  "require_user_input": boolean,     // true to prompt for input
  "content": "string",               // Message to display (markdown supported)
  "metadata": {
    "user_input": boolean,           // true to enable input
    "input_fields": [                // Array of input field definitions
      {
        "field_name": "string",      // Internal name for the field
        "field_description": "string", // User-facing prompt
        "field_values": [            // Array of options (dropdown) or [] (text input)
          "option1",
          "option2"
        ]
      }
    ]
  }
}
```

### Return Value Handling

- **Single field**: Returns the selected/entered value as a string
- **Multiple fields**: Returns a JSON object with all field values
- The CLI automatically sends this as the next message to the agent




