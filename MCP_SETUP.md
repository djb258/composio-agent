# MCP Server Setup for Render Monitoring

## Overview

This repo includes an MCP (Model Context Protocol) server that gives Claude direct access to monitor and control your Render deployment. This means Claude can:

- ✅ Check deployment status in real-time
- ✅ Fetch and analyze logs
- ✅ Trigger new deployments
- ✅ Update environment variables
- ✅ Monitor service health
- ✅ Fix issues automatically

## Quick Setup

### 1. Get Your Render API Key

1. Go to https://dashboard.render.com/u/settings#api-keys
2. Click **Create API Key**
3. Give it a name: `Claude MCP Access`
4. Copy the API key

### 2. Add API Key to Render Environment

1. Go to your service: https://dashboard.render.com/
2. Click **composio-imo-creator-url**
3. Go to **Environment** tab
4. Add these variables:

```
RENDER_API_KEY=<your-api-key-here>
RENDER_SERVICE_ID=srv-d3b7ikje5dus73cba2ng
```

5. Click **Save Changes** (triggers redeploy)

### 3. Configure Claude Code MCP

Once the service is deployed, add this MCP server to your Claude Code configuration:

```bash
claude mcp add \
  --transport http \
  --name render-monitor \
  --url https://composio-imo-creator-url.onrender.com/mcp \
  --header "Authorization: Bearer <RENDER_API_KEY>"
```

Or add manually to `~/.config/claude-code/mcp.json`:

```json
{
  "servers": {
    "render-monitor": {
      "transport": "http",
      "url": "https://composio-imo-creator-url.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer <YOUR_RENDER_API_KEY>"
      }
    }
  }
}
```

## Available MCP Tools

Once configured, Claude can use these tools:

### 1. `render_get_service_status`
Get current service status including deployment state.

**Example:**
```
Claude, check the Render service status
```

### 2. `render_get_latest_deploy`
Get information about the latest deployment.

**Example:**
```
Claude, what's the status of the latest deploy?
```

### 3. `render_get_logs`
Fetch recent logs from the service.

**Parameters:**
- `limit` (optional, default: 100) - Number of log lines

**Example:**
```
Claude, show me the last 50 log lines from Render
```

### 4. `render_list_deploys`
List recent deployments.

**Parameters:**
- `limit` (optional, default: 10) - Number of deployments

**Example:**
```
Claude, list the last 5 deployments
```

### 5. `render_trigger_deploy`
Trigger a new deployment.

**Parameters:**
- `clear_cache` (optional, default: false) - Clear build cache

**Example:**
```
Claude, trigger a new deployment with cache cleared
```

### 6. `render_get_env_vars`
List all environment variables (secrets are redacted).

**Example:**
```
Claude, what environment variables are set?
```

### 7. `render_update_env_var`
Update an environment variable.

**Parameters:**
- `key` (required) - Variable name
- `value` (required) - Variable value

**Example:**
```
Claude, update LOG_LEVEL to DEBUG
```

### 8. `render_get_metrics`
Get service metrics (requires paid Render plan).

**Example:**
```
Claude, show me the service metrics
```

## Usage Examples

### Monitor Deployment

```
You: Claude, check if the deployment is complete
Claude: [Uses render_get_latest_deploy]
The latest deployment (ID: dep-xyz) is "live" and completed at 2025-10-16T14:32:00Z.
The commit was: "fix: remove [standard] from uvicorn to avoid Rust compilation"
```

### Debug Issues

```
You: Claude, the service is failing, can you check the logs?
Claude: [Uses render_get_logs with limit=100]
I see the issue in the logs - there's a ModuleNotFoundError for 'mcp_server'.
Let me fix the imports and trigger a new deployment.
```

### Auto-Fix Deployments

```
You: Claude, fix the current deployment issue
Claude: [Analyzes logs, identifies issue, updates code, triggers deploy]
I've identified the problem - missing dependency. I've updated requirements.txt
and triggered a new deployment with cache cleared. Monitoring progress...
```

## MCP Endpoints

The MCP server exposes these endpoints:

### `GET /mcp/tools`
List all available MCP tools with their parameters.

```bash
curl https://composio-imo-creator-url.onrender.com/mcp/tools
```

### `POST /mcp/invoke`
Invoke an MCP tool.

```bash
curl -X POST https://composio-imo-creator-url.onrender.com/mcp/invoke \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <RENDER_API_KEY>" \
  -d '{
    "tool": "render_get_service_status",
    "parameters": {}
  }'
```

## Security

- **API Key Protection**: Store RENDER_API_KEY as a secret in Render environment variables
- **Authorization**: All MCP requests require the Authorization header with your Render API key
- **Secret Redaction**: Sensitive environment variables are automatically redacted in responses
- **HTTPS Only**: All communication is encrypted via HTTPS

## Troubleshooting

### MCP Tools Not Available

**Problem**: Claude says MCP tools aren't available

**Solution**:
1. Verify service is deployed and running
2. Check `/mcp/tools` endpoint is accessible
3. Verify RENDER_API_KEY is set in environment
4. Restart Claude Code to refresh MCP connections

### Authorization Failed

**Problem**: MCP calls return 401/403 errors

**Solution**:
1. Verify your Render API key is correct
2. Check the Authorization header is properly formatted
3. Ensure API key has correct permissions

### Service Status Shows as "suspended"

**Problem**: Free tier service suspended after inactivity

**Solution**:
```
Claude, trigger a new deployment to wake up the service
```

## Advanced Usage

### Continuous Monitoring

Set up Claude to monitor deployments automatically:

```
Claude, monitor the deployment every 30 seconds until it's complete,
then validate all endpoints and report any issues.
```

### Automated Deployment Pipeline

```
Claude, when I push to main:
1. Wait for Render to start building
2. Monitor the logs for errors
3. If build succeeds, validate all endpoints
4. If any endpoint fails, rollback and alert me
```

## API Reference

See the [Render API Documentation](https://api-docs.render.com/) for complete API details.

## Benefits

With MCP integration, you get:

- ⚡ **Real-time monitoring** - No need to check dashboard manually
- 🔧 **Auto-fixing** - Claude can identify and fix issues automatically
- 📊 **Log analysis** - Claude can parse logs and identify problems
- 🚀 **Faster deployments** - Claude can trigger and monitor deployments
- 🛡️ **Safety** - Claude can rollback failed deployments
- 📈 **Metrics** - Monitor service health and performance

---

**Ready to use?** Once the service is deployed with RENDER_API_KEY set, configure the MCP server in Claude Code and start monitoring!
