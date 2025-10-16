# Composio Agent Gateway

A FastAPI-based gateway service that acts as a proxy between your applications and the Composio API. This service provides a secure, validated, and monitored interface for executing Composio tools.

## Overview

The Composio Agent Gateway provides:
- **Health Monitoring**: `/status` endpoint for service health checks
- **Tool Discovery**: `/schema` endpoint listing all available tools
- **Tool Execution**: `/invoke` endpoint for secure tool invocations
- **Request Validation**: Automatic validation of required fields
- **Comprehensive Logging**: Full audit trail of all operations
- **Kill Switch**: Emergency shutdown capability

## Deployment Information

### Current Deployment
- **Service Name**: composio-imo-creator-url
- **Render URL**: https://composio-imo-creator-url.onrender.com
- **Repository**: https://github.com/djb258/composio-agent.git
- **Runtime**: Python 3.11.0
- **Deployment Date**: 2025-10-16

### Service Endpoints

```bash
# Health Check
https://composio-imo-creator-url.onrender.com/status

# Tool Schema
https://composio-imo-creator-url.onrender.com/schema

# Tool Invocation
https://composio-imo-creator-url.onrender.com/invoke
```

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/djb258/composio-agent.git
   cd composio-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your COMPOSIO_API_KEY
   ```

4. **Run the service**
   ```bash
   python main.py
   # Or with auto-reload:
   uvicorn main:app --reload --port 8000
   ```

5. **Test the endpoints**
   ```bash
   # Status check
   curl http://localhost:8000/status

   # Schema
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
         "timestamp_last_touched": "2025-10-16T12:00:00Z",
         "path": "/test/path"
       }
     }'
   ```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `COMPOSIO_API_KEY` | Your Composio API key | `sk_composio_xxx...` |
| `COMPOSIO_API_URL` | Composio API base URL | `https://api.composio.dev/api/v1` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_NAME` | Service identifier | `composio-agent` |
| `PORT` | Server port | `10000` (Render) / `8000` (local) |
| `KILL_SWITCH` | Emergency disable flag | `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Render Environment Configuration

The following variables are configured in Render Dashboard:

```bash
COMPOSIO_API_KEY=<your-actual-key>
COMPOSIO_API_URL=https://api.composio.dev/api/v1
SERVICE_NAME=composio-agent
KILL_SWITCH=false
PORT=10000
LOG_LEVEL=INFO
```

## API Documentation

### GET /status

Health check endpoint to verify service availability.

**Response:**
```json
{
  "status": "ok",
  "service": "composio-agent",
  "timestamp": "2025-10-16T12:00:00.000000",
  "kill_switch": false
}
```

### GET /schema

Returns JSON schema of all available tools with their parameters.

**Response:**
```json
{
  "tools": [
    {
      "name": "firebase_read",
      "description": "Read data from Firebase Realtime Database or Firestore",
      "endpoint": "/actions/firebase_read/execute",
      "method": "POST",
      "parameters": {...}
    },
    ...
  ]
}
```

### POST /invoke

Executes a tool by proxying to the Composio API.

**Request:**
```json
{
  "tool": "firebase_read",
  "data": {
    "agent_id": "agent_123",
    "process_id": "proc_456",
    "blueprint_id": "bp_789",
    "timestamp_last_touched": "2025-10-16T12:00:00Z",
    "path": "/users/123"
  }
}
```

**Success Response:**
```json
{
  "success": true,
  "result": {
    "data": {...}
  },
  "timestamp": "2025-10-16T12:00:01.234567",
  "execution_time": 0.234
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Missing required field: agent_id",
  "timestamp": "2025-10-16T12:00:01.234567"
}
```

### Required Fields Validation

All `/invoke` requests must include these fields in the `data` object:
- `agent_id` - Unique identifier for the agent
- `process_id` - Process identifier
- `blueprint_id` - Blueprint/template identifier
- `timestamp_last_touched` - Last modification timestamp (ISO 8601 format)

## Available Tools

The gateway supports the following Composio tools (see `config/mcp_endpoints.json` for full details):

1. **firebase_read** - Read data from Firebase
2. **firebase_write** - Write data to Firebase
3. **send_email** - Send email via configured service
4. **slack_message** - Send message to Slack channel
5. **http_request** - Make HTTP request to external API

## Project Structure

```
composio-agent/
├── main.py                     # FastAPI application
├── requirements.txt            # Python dependencies
├── Procfile                    # Render process command
├── render.yaml                 # Render deployment config
├── runtime.txt                 # Python version
├── config/
│   └── mcp_endpoints.json     # Tool definitions
├── .env.example               # Environment template
├── AGENT_BOOTSTRAP.md         # Architecture documentation
├── RENDER_COMPOSIO_DEPLOYMENT_GUIDE.md  # Deployment guide
└── README.md                  # This file
```

## Deployment to Render

### Prerequisites
- GitHub account with repository access
- Render.com account
- Composio API key

### Deployment Steps

1. **Connect Repository to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Select existing service: `composio-imo-creator-url`
   - Update repository connection to `djb258/composio-agent`

2. **Configure Environment Variables**
   - Go to service Environment tab
   - Add/verify all required variables (see Environment Variables section)
   - Save changes

3. **Deploy**
   - Click "Manual Deploy" → "Clear build cache & deploy"
   - Monitor build logs
   - Wait for deployment to complete

4. **Verify Deployment**
   ```bash
   # Test status endpoint
   curl -s https://composio-imo-creator-url.onrender.com/status

   # Expected response:
   # {"status":"ok","service":"composio-agent",...}

   # Test schema endpoint
   curl -s https://composio-imo-creator-url.onrender.com/schema
   ```

See `RENDER_COMPOSIO_DEPLOYMENT_GUIDE.md` for detailed deployment instructions.

## Testing

### Local Testing Script

```bash
#!/bin/bash
BASE_URL="http://localhost:8000"

echo "Testing /status..."
curl -s $BASE_URL/status | jq

echo -e "\nTesting /schema..."
curl -s $BASE_URL/schema | jq

echo -e "\nTesting /invoke..."
curl -s -X POST $BASE_URL/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "firebase_read",
    "data": {
      "agent_id": "test_agent",
      "process_id": "test_process",
      "blueprint_id": "test_blueprint",
      "timestamp_last_touched": "2025-10-16T12:00:00Z",
      "path": "/test"
    }
  }' | jq
```

### Production Testing Script

```bash
#!/bin/bash
BASE_URL="https://composio-imo-creator-url.onrender.com"

echo "Testing production /status..."
curl -s $BASE_URL/status | jq

echo -e "\nTesting production /schema..."
curl -s $BASE_URL/schema | jq
```

## Monitoring

### Logs

View logs in Render Dashboard:
1. Navigate to your service
2. Click "Logs" tab
3. View real-time application logs

### Health Checks

Render automatically monitors `/status` endpoint:
- Check Interval: Every 30 seconds
- Failure Threshold: 3 consecutive failures
- Auto-restart on failure

## Kill Switch

For emergency shutdown, set environment variable:
```bash
KILL_SWITCH=true
```

All `/invoke` requests will return:
```json
{
  "error": "service disabled",
  "status": "kill_switch_active"
}
```

## Security

- **API Keys**: Never commit `.env` files. Use `.env.example` as template
- **Validation**: All requests validated before proxying
- **Logging**: Full audit trail maintained
- **HTTPS**: Render provides automatic SSL
- **Environment Variables**: Sensitive data stored securely in Render

## Troubleshooting

### Build Failures
1. Check `requirements.txt` for correct package versions
2. Verify Python version in `runtime.txt`
3. Review build logs in Render Dashboard

### Runtime Errors
1. Verify environment variables are set correctly
2. Check Composio API key is valid
3. Review application logs
4. Test `/status` endpoint

### API Connection Issues
1. Verify `COMPOSIO_API_KEY` is correct
2. Check Composio API status
3. Review proxy logic in `main.py`

## ChatGPT Connector Setup

The Composio Agent Gateway is fully compatible with ChatGPT's MCP (Model Context Protocol) connector in Dev Mode.

### Discovery Endpoint

The service provides a ChatGPT-compatible plugin manifest at:
```
https://composio-imo-creator-url.onrender.com/.well-known/ai-plugin.json
```

### Connecting ChatGPT to the MCP Server

1. **Open ChatGPT Dev Mode**
   - Navigate to ChatGPT settings
   - Enable Developer Mode / Plugin Development Mode

2. **Add MCP Server Connection**
   - **MCP Server URL**: `https://composio-imo-creator-url.onrender.com`
   - **Authentication**: No Authentication (set `auth.type: none`)
   - **API Type**: OpenAPI
   - **OpenAPI Spec URL**: `https://composio-imo-creator-url.onrender.com/openapi.json`

3. **Verify Connection**
   ```bash
   # Test the discovery endpoint
   curl https://composio-imo-creator-url.onrender.com/.well-known/ai-plugin.json

   # Should return plugin manifest with schema_version, name, description, etc.
   ```

4. **Validate MCP Tools**
   - Once connected, ChatGPT can discover available tools via `/mcp/tools`
   - Test tool invocation via `/mcp/invoke`

   Example tools available:
   - `render_get_service_status` - Get Render service status
   - `render_get_latest_deploy` - Get latest deployment info
   - `render_get_logs` - Fetch service logs
   - `render_trigger_deploy` - Trigger new deployment
   - `firebase_read` - Read from Firebase
   - `firebase_write` - Write to Firebase
   - And more...

5. **Test MCP Integration**
   ```bash
   # List available MCP tools
   curl https://composio-imo-creator-url.onrender.com/mcp/tools

   # Invoke an MCP tool (requires Authorization header for Render tools)
   curl -X POST https://composio-imo-creator-url.onrender.com/mcp/invoke \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <RENDER_API_KEY>" \
     -d '{
       "tool": "render_get_service_status",
       "parameters": {}
     }'
   ```

### ChatGPT Usage Examples

Once connected, you can interact with the MCP server through ChatGPT:

```
You: "Check the status of my Render service"
ChatGPT: [Uses render_get_service_status tool]
Response: "Your service 'composio-imo-creator-url' is running with status 'not_suspended'..."

You: "Get the latest deployment information"
ChatGPT: [Uses render_get_latest_deploy tool]
Response: "The latest deployment (ID: dep-xyz) completed at... with status 'live'..."

You: "Trigger a new deployment"
ChatGPT: [Uses render_trigger_deploy tool]
Response: "New deployment initiated with ID: dep-abc..."
```

### Manifest Details

The `.well-known/ai-plugin.json` manifest includes:
- **schema_version**: `v1`
- **name_for_human**: "Composio Agent Gateway"
- **name_for_model**: "composio_agent"
- **description_for_human**: Unified MCP server for Composio, Render, and Firebase tools
- **auth**: No authentication required for discovery (tools may require auth)
- **api**: OpenAPI specification reference

### Troubleshooting ChatGPT Connection

**Problem**: ChatGPT returns 404 error when connecting

**Solution**:
1. Verify the discovery endpoint is accessible:
   ```bash
   curl https://composio-imo-creator-url.onrender.com/.well-known/ai-plugin.json
   ```
2. Ensure service is deployed and running
3. Check service logs for errors

**Problem**: MCP tools not discoverable

**Solution**:
1. Verify `/mcp/tools` endpoint:
   ```bash
   curl https://composio-imo-creator-url.onrender.com/mcp/tools
   ```
2. Check that MCP router is properly imported in `main.py`
3. Ensure `mcp_server.py` is deployed

**Problem**: Tool invocation fails

**Solution**:
1. For Render tools, ensure `RENDER_API_KEY` is set in environment variables
2. For Composio tools, verify `COMPOSIO_API_KEY` is configured
3. Check tool parameters match expected schema

## Support & Documentation

- [AGENT_BOOTSTRAP.md](AGENT_BOOTSTRAP.md) - Architecture details
- [RENDER_COMPOSIO_DEPLOYMENT_GUIDE.md](RENDER_COMPOSIO_DEPLOYMENT_GUIDE.md) - Deployment guide
- [MCP_SETUP.md](MCP_SETUP.md) - MCP server setup and usage
- [Composio Documentation](https://docs.composio.dev/)
- [Render Documentation](https://render.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## License

This project is provided as-is for use with Composio services.

## Version History

- **v1.0.0** (2025-10-16) - Initial release
  - FastAPI gateway implementation
  - Three core endpoints: status, schema, invoke
  - Request validation and logging
  - Kill switch functionality
  - Render deployment configuration
