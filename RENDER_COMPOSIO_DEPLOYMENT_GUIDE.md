# Render Composio Deployment Guide

## Overview
This guide walks through deploying the Composio Agent Gateway to Render.com, a cloud platform that simplifies application deployment.

## Prerequisites

- GitHub account with repository access
- Render.com account (free tier available)
- Composio API key

## Repository Setup

Ensure your repository contains:
```
composio-agent/
 ├── main.py                     # FastAPI application
 ├── requirements.txt            # Python dependencies
 ├── Procfile                    # Process command for Render
 ├── render.yaml                 # Render deployment configuration
 ├── runtime.txt                 # Python version specification
 ├── config/mcp_endpoints.json   # Tool definitions
 ├── .env.example                # Environment variable template
 ├── AGENT_BOOTSTRAP.md          # Architecture documentation
 └── README.md                   # Setup instructions
```

## Configuration Files

### Procfile
Defines the command to start your application:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### runtime.txt
Specifies Python version:
```
python-3.11.0
```

### render.yaml
Infrastructure as code for Render deployment:
```yaml
services:
  - type: web
    name: composio-agent
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: COMPOSIO_API_KEY
        sync: false
      - key: KILL_SWITCH
        value: false
      - key: LOG_LEVEL
        value: INFO
      - key: PYTHON_VERSION
        value: 3.11.0
    healthCheckPath: /status
    autoDeploy: true
```

## Deployment Steps

### Option 1: Deploy via Render Dashboard

1. **Connect Repository**
   - Log in to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select the `composio-agent` repository

2. **Configure Service**
   - Name: `composio-agent` (or your preferred name)
   - Runtime: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Set Environment Variables**
   - Click "Environment" tab
   - Add `COMPOSIO_API_KEY` with your Composio API key
   - Add `KILL_SWITCH` = `false`
   - Add `LOG_LEVEL` = `INFO`

4. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy your application
   - Monitor logs for successful deployment

### Option 2: Deploy via render.yaml (Blueprint)

1. **Prepare render.yaml**
   - Ensure `render.yaml` is in repository root
   - Commit and push to GitHub

2. **Create Blueprint**
   - Go to Render Dashboard
   - Click "Blueprints" → "New Blueprint Instance"
   - Select repository
   - Render reads `render.yaml` and creates services

3. **Configure Secrets**
   - Navigate to service settings
   - Add `COMPOSIO_API_KEY` in Environment section
   - Save changes (triggers redeploy)

## Environment Variables

Configure these in Render Dashboard under service Environment tab:

| Variable | Value | Secret? |
|----------|-------|---------|
| `COMPOSIO_API_KEY` | Your Composio API key | Yes |
| `KILL_SWITCH` | `false` | No |
| `LOG_LEVEL` | `INFO` or `DEBUG` | No |

## Health Checks

Render automatically monitors your service health:
- Health Check Path: `/status`
- Expected Response: `{"status":"ok","service":"composio-agent"}`
- Check Interval: Every 30 seconds
- Failure Threshold: 3 consecutive failures trigger restart

## Accessing Your Service

Once deployed, your service will be available at:
```
https://composio-agent.onrender.com
```
(Replace with your actual Render service URL)

### Test Endpoints

```bash
# Health check
curl https://composio-agent.onrender.com/status

# Get schema
curl https://composio-agent.onrender.com/schema

# Invoke tool
curl -X POST https://composio-agent.onrender.com/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "firebase_read",
    "data": {
      "agent_id": "agent_123",
      "process_id": "proc_456",
      "blueprint_id": "bp_789",
      "timestamp_last_touched": "2025-10-16T12:00:00Z"
    }
  }'
```

## Monitoring & Logs

### View Logs
1. Go to Render Dashboard
2. Select your service
3. Click "Logs" tab
4. View real-time application logs

### Metrics
Render provides:
- CPU usage
- Memory usage
- Request count
- Response times
- HTTP status codes

## Auto-Deploy

With `autoDeploy: true` in `render.yaml`:
- Every push to main branch triggers automatic deployment
- Render pulls latest code, rebuilds, and redeploys
- Zero-downtime deployments

## Troubleshooting

### Build Failures
- Check `requirements.txt` for correct package versions
- Ensure Python version in `runtime.txt` matches requirements
- Review build logs in Render Dashboard

### Runtime Errors
- Check environment variables are set correctly
- Verify `COMPOSIO_API_KEY` is valid
- Review application logs for error traces
- Test `/status` endpoint health

### Port Issues
- Ensure start command uses `$PORT` environment variable
- Render assigns port dynamically
- Never hardcode port numbers

### API Connection Issues
- Verify `COMPOSIO_API_KEY` is correct
- Check Composio API status
- Review proxy logic in `main.py`

## Scaling

Render free tier limitations:
- Service spins down after 15 minutes of inactivity
- First request after spin-down has cold start delay

Upgrade to paid tier for:
- Always-on instances
- Auto-scaling
- Increased resources
- Custom domains

## Security Best Practices

1. **Never commit secrets**: Use `.env.example`, not `.env`
2. **Use environment variables**: Store sensitive data in Render Environment settings
3. **Enable HTTPS**: Render provides free SSL certificates
4. **Implement authentication**: Add API key validation if needed
5. **Monitor logs**: Regular security audits via log analysis

## Rollback

If deployment fails or introduces bugs:
1. Go to Render Dashboard
2. Select service → "Events" tab
3. Find previous successful deployment
4. Click "Rollback"

## Custom Domains

To use custom domain:
1. Go to service Settings
2. Click "Custom Domains"
3. Add your domain
4. Configure DNS records as instructed
5. Render provisions SSL certificate automatically

## CI/CD Integration

For advanced workflows:
- Use Render API for programmatic deployments
- Integrate with GitHub Actions
- Add pre-deployment tests
- Configure staging environments

## Support

- [Render Documentation](https://render.com/docs)
- [Render Community Forum](https://community.render.com/)
- [Composio Documentation](https://docs.composio.dev/)

## Cost Estimates

- **Free Tier**: $0/month (with limitations)
- **Starter**: $7/month (always-on, 512MB RAM)
- **Standard**: $25/month (always-on, 2GB RAM)

See [Render Pricing](https://render.com/pricing) for latest details.
