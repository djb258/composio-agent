# Environment Variables Checklist

## Required for Render Deployment

Use this checklist to ensure all required environment variables are configured in your Render service.

### Pre-Migration Checklist

Before migrating to the `composio-agent` repository, verify these variables are set:

| Variable | Required | Secret? | Current Value | Status |
|----------|----------|---------|---------------|--------|
| `COMPOSIO_API_KEY` | ✅ Yes | ✅ Yes | `<your-key>` | ⬜ |
| `COMPOSIO_API_URL` | ✅ Yes | ❌ No | `https://api.composio.dev/api/v1` | ⬜ |
| `SERVICE_NAME` | ⚠️ Recommended | ❌ No | `composio-agent` | ⬜ |
| `KILL_SWITCH` | ⚠️ Recommended | ❌ No | `false` | ⬜ |
| `LOG_LEVEL` | ⚠️ Recommended | ❌ No | `INFO` | ⬜ |

### Automatic Variables (Set by Render)

These variables are automatically provided by Render and should NOT be manually configured:

| Variable | Description | Typical Value |
|----------|-------------|---------------|
| `PORT` | Service port | `10000` |
| `RENDER` | Render environment flag | `true` |
| `RENDER_SERVICE_NAME` | Service name | `composio-imo-creator-url` |
| `RENDER_EXTERNAL_URL` | Public URL | `https://composio-imo-creator-url.onrender.com` |

### Variable Details

#### COMPOSIO_API_KEY (Required)
- **Purpose**: Authentication key for Composio API
- **Format**: String (typically starts with `sk_composio_`)
- **Where to Get**: https://app.composio.dev/settings/api-keys
- **Mark as Secret**: ✅ Yes
- **Example**: `sk_composio_abc123def456...`

#### COMPOSIO_API_URL (Required)
- **Purpose**: Base URL for Composio API endpoints
- **Format**: URL string
- **Value**: `https://api.composio.dev/api/v1`
- **Mark as Secret**: ❌ No

#### SERVICE_NAME (Recommended)
- **Purpose**: Identifier for the service in logs and responses
- **Format**: String (lowercase, alphanumeric with hyphens)
- **Value**: `composio-agent`
- **Mark as Secret**: ❌ No

#### KILL_SWITCH (Recommended)
- **Purpose**: Emergency shutdown flag for /invoke endpoint
- **Format**: Boolean string (`true` or `false`)
- **Value**: `false` (default)
- **Mark as Secret**: ❌ No
- **Usage**: Set to `true` to disable all tool invocations

#### LOG_LEVEL (Recommended)
- **Purpose**: Logging verbosity
- **Format**: String (one of: DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Value**: `INFO` (production), `DEBUG` (development)
- **Mark as Secret**: ❌ No

## Setting Variables in Render Dashboard

### Via Web Interface

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Select service: `composio-imo-creator-url`
3. Navigate to **Environment** tab
4. Click **Add Environment Variable**
5. Enter **Key** and **Value**
6. Check **Secret** if sensitive
7. Click **Save Changes**

### Via Render API

```bash
# Set your Render API key
export RENDER_API_KEY="your-api-key"

# Set a variable
curl -X PUT "https://api.render.com/v1/services/srv-d3b7ikje5dus73cba2ng/env-vars/COMPOSIO_API_KEY" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"value": "your-actual-api-key-here"}'
```

## Verification Commands

### Check Local Environment

For local development, verify your `.env` file:

```bash
# Check if .env file exists
ls -la .env

# View non-secret variables
grep -v "API_KEY" .env

# Verify specific variable
grep COMPOSIO_API_URL .env
```

### Check Render Environment

Using Render API:

```bash
# List all environment variables
curl -X GET "https://api.render.com/v1/services/srv-d3b7ikje5dus73cba2ng/env-vars" \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

Via Dashboard:
1. Go to your service
2. Click **Environment** tab
3. Review all variables

## Post-Migration Verification

After migration, verify the service can access all variables:

### Test 1: Service Starts Successfully
```bash
# Check service status
curl https://composio-imo-creator-url.onrender.com/status

# Expected: {"status":"ok","service":"composio-agent",...}
```

### Test 2: API Key Is Loaded
Check Render logs for:
- ✅ No "COMPOSIO_API_KEY not set" warnings
- ✅ Service starts without configuration errors

### Test 3: Environment Variables Reflected
```bash
# Status endpoint should reflect variables
curl https://composio-imo-creator-url.onrender.com/status

# Check kill_switch value
# Should match your KILL_SWITCH variable
```

## Troubleshooting

### Error: "COMPOSIO_API_KEY not set"
**Solution**:
1. Go to Render Dashboard → Environment
2. Add `COMPOSIO_API_KEY` variable
3. Mark as **Secret**
4. Save (triggers auto-redeploy)

### Error: "Service configuration error"
**Solution**:
1. Verify all required variables are set
2. Check for typos in variable names
3. Ensure values are properly formatted
4. Review Render logs for specific error

### Variables Not Taking Effect
**Solution**:
1. After adding/updating variables, trigger manual deploy
2. Clear build cache if needed
3. Verify variables in Environment tab
4. Check deployment logs for variable loading

## Security Best Practices

### ✅ Do's
- ✅ Mark `COMPOSIO_API_KEY` as **Secret**
- ✅ Use `.env` file for local development
- ✅ Add `.env` to `.gitignore`
- ✅ Use `.env.example` as template
- ✅ Rotate API keys regularly
- ✅ Use different keys for dev/staging/prod

### ❌ Don'ts
- ❌ Never commit `.env` files
- ❌ Never hardcode API keys in source code
- ❌ Never share API keys in plain text
- ❌ Never log API keys
- ❌ Never expose keys in error messages

## Environment-Specific Configurations

### Local Development
```bash
# .env
COMPOSIO_API_KEY=sk_composio_dev_key
COMPOSIO_API_URL=https://api.composio.dev/api/v1
SERVICE_NAME=composio-agent-local
KILL_SWITCH=false
LOG_LEVEL=DEBUG
PORT=8000
```

### Production (Render)
```bash
# Via Render Dashboard Environment Tab
COMPOSIO_API_KEY=sk_composio_prod_key
COMPOSIO_API_URL=https://api.composio.dev/api/v1
SERVICE_NAME=composio-agent
KILL_SWITCH=false
LOG_LEVEL=INFO
# PORT is set automatically by Render
```

## Quick Reference

### Minimum Required Variables
```bash
COMPOSIO_API_KEY=<your-key>
COMPOSIO_API_URL=https://api.composio.dev/api/v1
```

### Recommended Full Set
```bash
COMPOSIO_API_KEY=<your-key>
COMPOSIO_API_URL=https://api.composio.dev/api/v1
SERVICE_NAME=composio-agent
KILL_SWITCH=false
LOG_LEVEL=INFO
```

## Migration Day Checklist

Before migrating:
- [ ] Export current environment variables from old service
- [ ] Document all variable values (securely)
- [ ] Prepare new repository with `.env.example`

During migration:
- [ ] Update repository connection
- [ ] Verify all variables in Environment tab
- [ ] Add any missing variables
- [ ] Trigger manual deploy

After migration:
- [ ] Test `/status` endpoint
- [ ] Verify logs show no configuration errors
- [ ] Run validation scripts
- [ ] Monitor service for 24 hours

---

**Last Updated**: 2025-10-16
