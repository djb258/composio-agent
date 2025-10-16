# Render Deployment Troubleshooting Guide

## Common Render Deployment Issues & Solutions

This guide addresses the most common pain points when deploying to Render.

---

## Issue 1: Build Fails - "Could not find a version that satisfies the requirement"

### Symptoms
```
ERROR: Could not find a version that satisfies the requirement fastapi==0.109.0
ERROR: No matching distribution found for fastapi==0.109.0
```

### Solutions

**Option A: Update package versions**
```bash
# Locally, update requirements
pip freeze > requirements.txt

# Or use more flexible versions
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
```

**Option B: Use Python version compatible with packages**
```
# In runtime.txt, try:
python-3.11.0
# or
python-3.10.13
```

**Option C: Clear build cache**
- Go to Render Dashboard
- Manual Deploy → **Clear build cache & deploy**

---

## Issue 2: Build Succeeds But Service Won't Start

### Symptoms
```
Application startup failed
Service unhealthy
```

### Common Causes & Fixes

#### 2A: Port Configuration Issue
**Problem**: Service not listening on `$PORT`

**Fix**: Verify `Procfile` or start command uses `$PORT`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**NOT**:
```
web: uvicorn main:app --host 0.0.0.0 --port 8000  # WRONG - hardcoded port
```

#### 2B: Missing Environment Variables
**Problem**: `COMPOSIO_API_KEY` not set

**Fix**:
1. Go to Environment tab
2. Add `COMPOSIO_API_KEY`
3. Mark as **Secret**
4. Save (triggers redeploy)

**Check logs for**:
```
COMPOSIO_API_KEY not set - /invoke endpoint will fail
```

#### 2C: Import Errors
**Problem**: Missing dependencies or wrong Python version

**Fix**:
```bash
# Verify requirements.txt includes all imports
# Check main.py imports match installed packages

# Common missing packages:
python-dotenv  # For .env file support
httpx         # For HTTP requests
```

---

## Issue 3: Service Starts But Health Check Fails

### Symptoms
```
Health check failed
Service restarting continuously
```

### Solutions

#### 3A: Verify Health Check Path
**In render.yaml or Dashboard Settings**:
```yaml
healthCheckPath: /status
```

**Test endpoint locally first**:
```bash
curl http://localhost:8000/status
# Should return: {"status":"ok",...}
```

#### 3B: Health Check Timeout
**Problem**: `/status` endpoint too slow

**Fix**: Increase health check timeout in render.yaml:
```yaml
services:
  - type: web
    healthCheckPath: /status
    healthCheckTimeout: 10  # seconds
```

#### 3C: Wrong HTTP Method
**Ensure health check endpoint**:
- Accepts GET requests
- Returns 200 status code
- Returns valid JSON

---

## Issue 4: Deployment Works But Endpoints Return Errors

### Symptoms
```
500 Internal Server Error
502 Bad Gateway
503 Service Unavailable
```

### Solutions

#### 4A: Check Application Logs
```
Render Dashboard → Logs tab
```

**Look for**:
- Python exceptions
- Import errors
- Configuration errors
- API connection failures

#### 4B: Test Environment Variables
**Add debug endpoint temporarily**:
```python
@app.get("/debug")
async def debug():
    return {
        "api_key_set": bool(os.getenv("COMPOSIO_API_KEY")),
        "api_url": os.getenv("COMPOSIO_API_URL"),
        "kill_switch": os.getenv("KILL_SWITCH")
    }
```

#### 4C: Verify Composio API Access
**Test API key separately**:
```bash
curl -H "X-API-Key: your-key" https://api.composio.dev/api/v1/actions
```

---

## Issue 5: "Your service isn't responding to HTTP requests"

### Symptoms
```
Your service isn't responding to HTTP requests on port 10000
```

### Solutions

#### 5A: Verify Start Command
**Must bind to 0.0.0.0 (not localhost)**:
```
✓ CORRECT: uvicorn main:app --host 0.0.0.0 --port $PORT
✗ WRONG:   uvicorn main:app --host 127.0.0.1 --port $PORT
✗ WRONG:   python main.py  # if it binds to localhost
```

#### 5B: Check if App is Running
**In logs, look for**:
```
Uvicorn running on http://0.0.0.0:10000
Application startup complete
```

#### 5C: Firewall/Network Issues
**Render handles this automatically, but ensure**:
- No custom firewall rules in code
- Not blocking external connections

---

## Issue 6: Environment Variables Not Loading

### Symptoms
```
None value for required variable
KeyError: 'COMPOSIO_API_KEY'
```

### Solutions

#### 6A: Verify Variables in Dashboard
1. Environment tab
2. Check variable name matches exactly (case-sensitive)
3. No extra spaces
4. Value not empty

#### 6B: Redeploy After Adding Variables
**Environment variable changes require redeploy**:
- Save variables
- Manual Deploy → Deploy

#### 6C: Use python-dotenv Correctly
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Only loads .env locally, not on Render
api_key = os.getenv("COMPOSIO_API_KEY")
```

**Note**: Render sets env vars directly, `.env` file not needed in production

---

## Issue 7: Build Takes Forever / Timeouts

### Symptoms
```
Build timeout after 15 minutes
Build killed
```

### Solutions

#### 7A: Optimize requirements.txt
**Remove unused packages**:
```bash
# Only include what you actually use
fastapi==0.109.0
uvicorn[standard]==0.27.0
httpx==0.26.0
pydantic==2.5.3
python-dotenv==1.0.0
```

#### 7B: Use Build Cache
**Don't clear cache every time**:
- Only clear if you have persistent issues
- Normal deploys should use cache

#### 7C: Check for Heavy Dependencies
**Avoid**:
- Large ML libraries (tensorflow, pytorch) unless needed
- Unnecessary database drivers
- Development tools in production

---

## Issue 8: "This service is currently unavailable"

### Symptoms
- Service shows as deployed
- URL returns 503 error
- Render dashboard shows "Live"

### Solutions

#### 8A: Free Tier Spin Down
**If using free tier**:
- Service spins down after 15 min inactivity
- First request after spin down takes ~30 seconds
- Solution: Upgrade to paid tier or accept cold starts

#### 8B: Service Crashed
**Check recent logs**:
- Look for exceptions
- Check last log timestamp
- Restart service manually if needed

---

## Pre-Deployment Checklist

Run through this before deploying to avoid common issues:

### Code Review
- [ ] `Procfile` exists and uses `$PORT`
- [ ] `runtime.txt` specifies Python version
- [ ] `requirements.txt` has all dependencies
- [ ] `main.py` has no syntax errors
- [ ] Health check endpoint (`/status`) works locally

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Set env vars
export COMPOSIO_API_KEY="test-key"
export COMPOSIO_API_URL="https://api.composio.dev/api/v1"

# Run server
uvicorn main:app --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/status
curl http://localhost:8000/schema
```

### Git Repository
- [ ] All files committed
- [ ] Pushed to main branch
- [ ] `.env` not committed (in `.gitignore`)
- [ ] `.env.example` included

### Render Settings
- [ ] Repository connected
- [ ] Branch set to `main`
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Health check path: `/status`
- [ ] All environment variables set

---

## Emergency Rollback

If deployment completely breaks:

### Quick Rollback Steps

1. **Render Dashboard → Events tab**
2. **Find previous successful deploy**
3. **Click "Rollback to this deploy"**
4. **Confirm rollback**

### Alternative: Revert Git Commit

```bash
# Find last working commit
git log --oneline

# Revert to it
git revert <commit-hash>
git push origin main

# Render auto-deploys
```

---

## Common Render-Specific Gotchas

### 1. Environment Variables Timing
- Variables added AFTER service creation require manual redeploy
- Save → Wait → Manual Deploy

### 2. Port Binding
- MUST use `$PORT` environment variable
- MUST bind to `0.0.0.0` not `localhost`

### 3. Health Checks
- Must return 200 status
- Must be HTTP GET (not POST)
- Must respond within timeout (default 10s)

### 4. File System
- Render filesystem is ephemeral
- Don't store data in local files
- Use external databases/storage

### 5. Build Cache
- Clearing cache fixes many issues
- But increases build time
- Only clear when necessary

---

## Debug Mode Deployment

If all else fails, deploy with extra logging:

### In main.py, add:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add startup logging
@app.on_event("startup")
async def startup_event():
    logger.info("=== APPLICATION STARTING ===")
    logger.info(f"COMPOSIO_API_KEY set: {bool(os.getenv('COMPOSIO_API_KEY'))}")
    logger.info(f"COMPOSIO_API_URL: {os.getenv('COMPOSIO_API_URL')}")
    logger.info(f"PORT: {os.getenv('PORT')}")
    logger.info(f"Kill switch: {os.getenv('KILL_SWITCH')}")
    logger.info("=== STARTUP COMPLETE ===")
```

Monitor logs for these startup messages.

---

## Getting Help

If issues persist:

1. **Check Render Status**: https://status.render.com/
2. **Render Community**: https://community.render.com/
3. **Review Logs**: Render Dashboard → Logs (download full log)
4. **Support**: help@render.com (paid plans only)

---

## Success Indicators

You'll know deployment succeeded when:

✅ Build logs show: `Build successful`
✅ Service shows: **Live** (green dot)
✅ Logs show: `Uvicorn running on http://0.0.0.0:10000`
✅ Logs show: `Application startup complete`
✅ Health check: `Healthy` ✓
✅ URL responds: `curl <your-url>/status` returns 200

---

**Pro Tip**: Keep a terminal with `curl https://your-service.onrender.com/status` running during deployment. As soon as it returns 200, you're good!
