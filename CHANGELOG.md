# Changelog

All notable changes to agent-chat-cli will be documented in this file.

## [0.2.14] - 2025-11-05

### Added
- Version display on CLI startup (`🚀 agent-chat-cli v0.2.14`)
- `--version` flag to display CLI version

### Fixed
- **Major**: Fixed duplicate response panel issue - final response now displayed only once
- **Major**: Fixed tool notification text appearing in final response - status messages now excluded from response buffer
- **Major**: Fixed streaming output accumulation - now properly accumulates with smart space insertion
- Improved JSON payload parsing with proper brace matching for nested objects
- Enhanced text sanitization to handle escaped newlines (`\n` → actual newlines)

### Changed
- Streaming text chunks now accumulate with intelligent spacing
- Final response preparation moved outside Live context to prevent duplicate display
- Separated `final_response_text` from `response_markdown` for cleaner display logic

### Technical Details
- Status messages (TaskStatusUpdateEvent) are now treated as metadata and excluded from response buffer
- Only artifact text (streaming_result, partial_result, etc.) is processed for display
- Smart space insertion between chunks: adds space only when boundaries lack whitespace
- Improved brace matching algorithm for JSON extraction in sanitize_stream_text

## [0.2.13] - Previous

### Features
- Multi-protocol support (A2A/MCP)
- Real-time streaming output with Rich UI
- Execution plan, tool activity, and response panels
- Server-Sent Events (SSE) support for A2A protocol
- Token-by-token streaming display

