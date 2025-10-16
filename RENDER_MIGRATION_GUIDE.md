# Render Service Migration Guide
## Migrating from imo-creator to composio-agent

This guide provides step-by-step instructions for migrating your existing Render service to the new `composio-agent` repository.

## Migration Overview

**Current Service Details:**
- **Service Name**: composio-imo-creator-url
- **Service ID**: srv-d3b7ikje5dus73cba2ng
- **Current Repo**: https://github.com/djb258/imo-creator.git
- **New Repo**: https://github.com/djb258/composio-agent.git
- **Runtime**: Python 3.11.0
- **Live URL**: https://composio-imo-creator-url.onrender.com

**Migration Strategy:**
- Keep the same Render service (same URL, same service ID)
- Update the connected GitHub repository
- Preserve all environment variables
- Clear build cache for clean deployment
- Verify endpoints post-migration

## Prerequisites

1. Access to Render Dashboard with appropriate permissions
2. GitHub repository `composio-agent` is ready with all files
3. Composio API key available
4. Git repository pushed to main branch

## Migration Steps

### Step 1: Verify New Repository

Before migrating, ensure your new repository is ready:

```bash
# Check that all files are committed
cd composio-agent
git status

# Verify key files exist
ls -la main.py requirements.txt Procfile render.yaml runtime.txt config/mcp_endpoints.json

# Push to main if needed
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Update Repository Connection in Render Dashboard

**Via Render Dashboard (Recommended):**

1. Log in to [Render Dashboard](https://dashboard.render.com/)
2. Navigate to your service: **composio-imo-creator-url**
3. Click on **Settings** tab
4. Scroll to **Repository** section
5. Click **Update Repository** or **Connect Repository**
6. Select or reconnect: `djb258/composio-agent`
7. Ensure branch is set to: `main`
8. Click **Save**

### Step 3: Verify Build Configuration

In the Render Dashboard Settings, verify:

| Setting | Value |
|---------|-------|
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/status` |
| **Auto-Deploy** | Enabled |

If any are incorrect, update them and save.

### Step 4: Verify Environment Variables

Navigate to the **Environment** tab and verify these variables exist:

```bash
COMPOSIO_API_KEY=<your-actual-api-key>
COMPOSIO_API_URL=https://api.composio.dev/api/v1
SERVICE_NAME=composio-agent
KILL_SWITCH=false
LOG_LEVEL=INFO
```

**Important Notes:**
- `PORT` is automatically set by Render (typically 10000)
- `PYTHON_VERSION` is set via `runtime.txt` file
- Do NOT include `PORT` in environment variables unless required

### Step 5: Add/Update Missing Environment Variables

If any variables are missing:

1. Click **Add Environment Variable**
2. Enter **Key** and **Value**
3. Click **Add** for each variable
4. Click **Save Changes** when done

**Environment Variable Template:**

| Key | Value | Secret? |
|-----|-------|---------|
| COMPOSIO_API_KEY | `<your-key>` | ✅ Yes |
| COMPOSIO_API_URL | `https://api.composio.dev/api/v1` | ❌ No |
| SERVICE_NAME | `composio-agent` | ❌ No |
| KILL_SWITCH | `false` | ❌ No |
| LOG_LEVEL | `INFO` | ❌ No |

### Step 6: Trigger Manual Deploy with Cache Clear

1. Go to **Manual Deploy** section (top right)
2. Select: **Clear build cache & deploy**
3. Click **Deploy**
4. Monitor the **Logs** tab for build progress

**Expected Build Process:**
```
Building...
Installing dependencies from requirements.txt
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- httpx==0.26.0
- pydantic==2.5.3
- python-dotenv==1.0.0

Build successful
Starting service...
Application startup complete
Uvicorn running on http://0.0.0.0:10000
```

### Step 7: Monitor Deployment

Watch the logs for:
- ✅ Dependencies installed successfully
- ✅ No import errors
- ✅ Server started on correct port
- ✅ Health check passing

**Typical deployment time**: 2-5 minutes

### Step 8: Verify Endpoints

Once deployment shows as **Live**, test the endpoints:

#### Test /status endpoint
```bash
curl -s https://composio-imo-creator-url.onrender.com/status
```

**Expected Response:**
```json
{
  "status": "ok",
  "service": "composio-agent",
  "timestamp": "2025-10-16T...",
  "kill_switch": false
}
```

#### Test /schema endpoint
```bash
curl -s https://composio-imo-creator-url.onrender.com/schema
```

**Expected Response:**
```json
{
  "tools": [
    {
      "name": "firebase_read",
      "description": "...",
      ...
    },
    ...
  ]
}
```

#### Test /invoke endpoint (optional)
```bash
curl -X POST https://composio-imo-creator-url.onrender.com/invoke \
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
  }'
```

### Step 9: Update Documentation

Update your `README.md` with migration confirmation:

```markdown
## Deployment Confirmation

- **Migration Date**: 2025-10-16
- **Service ID**: srv-d3b7ikje5dus73cba2ng
- **Repository**: https://github.com/djb258/composio-agent.git
- **Live URL**: https://composio-imo-creator-url.onrender.com
- **Status**: ✅ Successfully deployed and verified
- **Endpoints Verified**:
  - ✅ /status - Returns 200 OK
  - ✅ /schema - Returns tool definitions
  - ✅ /invoke - Accepts requests
```

Commit and push:
```bash
git add README.md
git commit -m "docs: confirm successful Render migration"
git push origin main
```

## Alternative: Using Render API (Advanced)

If you prefer API-based migration:

### Get Your Render API Key

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Account Settings → API Keys
3. Create new API key or copy existing

### Update Service Repository via API

```bash
# Set your API key
export RENDER_API_KEY="your-api-key-here"

# Update service repository
curl -X PATCH "https://api.render.com/v1/services/srv-d3b7ikje5dus73cba2ng" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "serviceDetails": {
      "repo": "https://github.com/djb258/composio-agent",
      "branch": "main"
    }
  }'
```

### List Environment Variables via API

```bash
curl -X GET "https://api.render.com/v1/services/srv-d3b7ikje5dus73cba2ng/env-vars" \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

### Set Environment Variable via API

```bash
curl -X PUT "https://api.render.com/v1/services/srv-d3b7ikje5dus73cba2ng/env-vars/COMPOSIO_API_KEY" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "value": "your-api-key-here"
  }'
```

### Trigger Deploy via API

```bash
curl -X POST "https://api.render.com/v1/services/srv-d3b7ikje5dus73cba2ng/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "clearCache": "clear"
  }'
```

## Troubleshooting

### Build Fails

**Error**: `Could not find a version that satisfies the requirement`

**Solution**:
- Check `requirements.txt` for correct package versions
- Verify Python version in `runtime.txt` matches dependencies

### Service Won't Start

**Error**: `Application startup failed`

**Solution**:
- Check logs for import errors
- Verify `COMPOSIO_API_KEY` is set
- Check `main.py` for syntax errors

### Health Check Failing

**Error**: `Health check failed`

**Solution**:
- Verify `/status` endpoint returns 200 OK
- Check if service is listening on correct port (`$PORT`)
- Review application logs for errors

### Environment Variables Missing

**Solution**:
1. Go to Environment tab
2. Add missing variables from checklist
3. Save changes (triggers auto-redeploy)

### Old Code Still Running

**Solution**:
1. Verify repository connection updated
2. Clear build cache
3. Trigger manual deploy
4. Check latest deploy SHA in logs matches your repo

## Verification Checklist

After migration, verify:

- [ ] Repository connection shows `djb258/composio-agent`
- [ ] Branch set to `main`
- [ ] All environment variables present
- [ ] Build completed successfully
- [ ] Service shows as "Live"
- [ ] `/status` returns `{"status":"ok","service":"composio-agent"}`
- [ ] `/schema` returns tool definitions
- [ ] `/invoke` accepts requests
- [ ] Logs show no errors
- [ ] Health checks passing
- [ ] URL unchanged: https://composio-imo-creator-url.onrender.com

## Rollback Plan

If migration fails and you need to rollback:

1. Go to Render Dashboard → Settings
2. Update repository back to: `djb258/imo-creator`
3. Restore previous environment variables if changed
4. Clear cache and deploy
5. Verify old service is working

## Post-Migration Tasks

1. ✅ Update any documentation referencing old repo
2. ✅ Inform team members of new repository location
3. ✅ Archive or delete old `imo-creator` repo (optional)
4. ✅ Update CI/CD pipelines if applicable
5. ✅ Monitor service logs for 24-48 hours post-migration

## Support

- **Render Documentation**: https://render.com/docs
- **Render API Reference**: https://api-docs.render.com/
- **Composio Documentation**: https://docs.composio.dev/

## Migration Validation Script

See `scripts/validate-deployment.sh` for automated post-migration validation.

---

**Migration completed successfully?** Update this document with actual timestamps and verification screenshots!
