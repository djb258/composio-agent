# Deploy Now - Quick Start Guide

## What's Been Updated

✅ **Procfile** - Changed to `python main.py` (matches imo-creator)
✅ **runtime.txt** - Updated to `python-3.11.9` (matches imo-creator)
✅ **render.yaml** - Updated with working config from imo-creator
✅ **main.py** - Added `/health` endpoint for Render health checks
✅ **All files** - Ready for deployment

## Deployment Steps (5 Minutes)

### Step 1: Commit and Push to GitHub

```bash
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\composio-agent"

git add .
git commit -m "feat: update configs to match working imo-creator setup"
git push origin main
```

### Step 2: Update Render Service

1. Go to https://dashboard.render.com/
2. Click on service: **composio-imo-creator-url**
3. Go to **Settings** tab
4. Scroll to **Repository** section
5. Click **Disconnect** or **Update Repository**
6. Select: **djb258/composio-agent**
7. Branch: **main**
8. Click **Save**

### Step 3: Verify Environment Variables

Still in Render Dashboard:

1. Click **Environment** tab
2. **Verify these exist** (add if missing):

```
COMPOSIO_API_KEY = <your-actual-api-key>
COMPOSIO_API_URL = https://api.composio.dev/api/v1
SERVICE_NAME = composio-agent
KILL_SWITCH = false
LOG_LEVEL = INFO
PYTHONUNBUFFERED = 1
```

3. Click **Save Changes**

### Step 4: Deploy

1. Click **Manual Deploy** (top right)
2. Select: **Clear build cache & deploy**
3. Click **Deploy**

### Step 5: Monitor Deployment

Watch the **Logs** tab for:

```
✓ Installing dependencies
✓ Build successful
✓ Starting service...
✓ Uvicorn running on http://0.0.0.0:10000
✓ Application startup complete
```

### Step 6: Test Endpoints

Once it shows "Live" (green dot):

```bash
# Test health endpoint
curl https://composio-imo-creator-url.onrender.com/health

# Expected: {"status":"healthy","service":"composio-agent",...}

# Test status endpoint
curl https://composio-imo-creator-url.onrender.com/status

# Test schema endpoint
curl https://composio-imo-creator-url.onrender.com/schema
```

Or use PowerShell:

```powershell
# Test health
Invoke-RestMethod https://composio-imo-creator-url.onrender.com/health

# Test status
Invoke-RestMethod https://composio-imo-creator-url.onrender.com/status

# Test schema
Invoke-RestMethod https://composio-imo-creator-url.onrender.com/schema
```

### Step 7: Run Validation Script

```powershell
cd "C:\Users\CUSTOM PC\Desktop\Cursor Builds\composio-agent"
powershell -File scripts\validate-deployment.ps1
```

## What Changed From Original Config

| File | Original | Updated | Why |
|------|----------|---------|-----|
| `Procfile` | `uvicorn main:app --host 0.0.0.0 --port $PORT` | `python main.py` | Matches imo-creator proven config |
| `runtime.txt` | `python-3.11.0` | `python-3.11.9` | Matches imo-creator Python version |
| `render.yaml` | Basic config | Full imo-creator config | Includes plan, region, PYTHONUNBUFFERED |
| `main.py` | `/status` only | `/health` + `/status` | Render health check expects `/health` |

## Key Configuration from imo-creator

Based on your working imo-creator deployment:

- **Start Command**: `python main.py` (not uvicorn directly)
- **Python Version**: 3.11.9
- **Health Check**: `/health` endpoint
- **Region**: Oregon
- **Plan**: Free tier
- **Environment**: Includes `PYTHONUNBUFFERED=1` for immediate log output

## Troubleshooting

### If Build Fails

Check logs for:
- Missing packages → verify requirements.txt
- Python version issues → runtime.txt should be 3.11.9

### If Service Won't Start

Check logs for:
- "COMPOSIO_API_KEY not set" → Add in Environment tab
- Port binding issues → Ensure main.py uses `$PORT`
- Import errors → Check requirements.txt

### If Health Check Fails

- Verify `/health` endpoint exists ✓ (already added)
- Check service is listening on correct port
- Review logs for startup errors

## Success Indicators

You'll know it worked when:

✅ Build logs show: `Build successful`
✅ Service status: **Live** (green dot)
✅ Logs show: `Uvicorn running on http://0.0.0.0:10000`
✅ Health check: **Healthy** ✓
✅ `/health` returns: `{"status":"healthy",...}`
✅ `/status` returns: `{"status":"ok","service":"composio-agent",...}`
✅ `/schema` returns: `{"tools":[...]}`

## Rollback Plan

If something goes wrong:

1. Render Dashboard → **Events** tab
2. Find last working deploy
3. Click **Rollback to this deploy**

Or revert Git:

```bash
git revert HEAD
git push origin main
```

## Post-Deployment

After successful deployment:

1. Test all three endpoints
2. Run validation script
3. Monitor logs for 10-15 minutes
4. Check for any errors or warnings
5. Verify ChatGPT Dev Mode can connect

## Expected Deployment Time

- Build: 2-3 minutes
- Deploy: 1 minute
- Health check: 30 seconds
- **Total**: ~4-5 minutes

## Support

If issues persist:

1. Check **RENDER_TROUBLESHOOTING.md** for common issues
2. Review logs in Render Dashboard
3. Verify environment variables
4. Test endpoints manually

---

**Ready to deploy?** Follow the steps above and you'll have a working Composio agent gateway in ~5 minutes using the proven imo-creator configuration!
