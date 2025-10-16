# Composio Agent Bootstrap Guide

## Overview
This document outlines the architecture and setup for the Composio Agent Gateway - a FastAPI-based service that acts as a proxy between your application and the Composio API.

## Architecture

### Components
1. **FastAPI Service**: Main application server
2. **MCP Endpoints Configuration**: JSON file defining available tools
3. **Composio API Integration**: Proxy layer for tool invocations
4. **Environment Configuration**: Secure API key management

### Endpoints

#### GET /status
Health check endpoint to verify service availability.

**Response:**
```json
{
  "status": "ok",
  "service": "composio-agent"
}
```

#### GET /schema
Returns JSON listing all available tool definitions.

**Response:**
```json
{
  "tools": [
    {
      "name": "firebase_read",
      "description": "Read data from Firebase",
      "parameters": {...}
    },
    {
      "name": "firebase_write",
      "description": "Write data to Firebase",
      "parameters": {...}
    }
  ]
}
```

#### POST /invoke
Executes a tool by proxying to Composio API.

**Request:**
```json
{
  "tool": "firebase_read",
  "data": {
    "agent_id": "agent_123",
    "process_id": "proc_456",
    "blueprint_id": "bp_789",
    "timestamp_last_touched": "2025-10-16T12:00:00Z",
    ...
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {...},
  "timestamp": "2025-10-16T12:00:01Z"
}
```

### Validation Rules

The `/invoke` endpoint validates the following required fields:
- `agent_id`: Unique identifier for the agent
- `process_id`: Process identifier
- `blueprint_id`: Blueprint/template identifier
- `timestamp_last_touched`: Last modification timestamp

If any field is missing, returns:
```json
{
  "error": "Missing required field: <field_name>",
  "status": "validation_failed"
}
```

### Kill Switch

The service supports a `KILL_SWITCH` environment variable for emergency shutdown:
- When `KILL_SWITCH=true`, all `/invoke` requests return:
```json
{
  "error": "service disabled",
  "status": "kill_switch_active"
}
```

### Logging

All invocations are logged with:
- Input parameters
- Output results
- Error messages (if any)
- Timestamps
- Execution duration

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `COMPOSIO_API_KEY` | API key for Composio service | Yes |
| `KILL_SWITCH` | Emergency disable flag | No |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | No (default: INFO) |
| `PORT` | Service port | No (default: 8000) |

## Tool Definitions

Tools are defined in `config/mcp_endpoints.json`. Each tool should include:
- `name`: Unique tool identifier
- `description`: What the tool does
- `endpoint`: Composio API endpoint
- `method`: HTTP method (GET, POST, etc.)
- `parameters`: Expected input schema

## Security Considerations

1. **API Key Management**: Never commit `.env` files. Use `.env.example` as template.
2. **Validation**: Always validate required fields before proxying requests
3. **Kill Switch**: Provides emergency stop mechanism
4. **Logging**: Maintain audit trail of all operations
5. **Error Handling**: Don't expose internal errors to clients

## Development Workflow

1. Clone repository
2. Copy `.env.example` to `.env` and configure
3. Install dependencies: `pip install -r requirements.txt`
4. Run locally: `python main.py` or `uvicorn main:app --reload`
5. Test endpoints using provided curl commands
6. Deploy to Render using `render.yaml`

## Testing

### Local Testing
```bash
# Status check
curl http://localhost:8000/status

# Schema check
curl http://localhost:8000/schema

# Invoke tool
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "firebase_read",
    "data": {
      "agent_id": "test_agent",
      "process_id": "test_process",
      "blueprint_id": "test_blueprint",
      "timestamp_last_touched": "2025-10-16T12:00:00Z"
    }
  }'
```

## Deployment

See `RENDER_COMPOSIO_DEPLOYMENT_GUIDE.md` for detailed deployment instructions.
