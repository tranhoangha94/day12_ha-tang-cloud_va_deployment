# Deployment Information

## Public URL

https://day12-ha-tang-cloud-va-deployment.vercel.app

## Platform

Vercel (serverless FastAPI — ASGI native, Python 3.11)

## Test Commands

### Health Check

```bash
curl https://day12-ha-tang-cloud-va-deployment.vercel.app/health
# Expected: {"status":"ok",...}
```

```powershell
Invoke-RestMethod https://day12-ha-tang-cloud-va-deployment.vercel.app/health
Invoke-RestMethod https://day12-ha-tang-cloud-va-deployment.vercel.app/ready
```

### API Test (with authentication)

```bash
curl -X POST https://day12-ha-tang-cloud-va-deployment.vercel.app/ask \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

```powershell
Invoke-RestMethod -Uri https://day12-ha-tang-cloud-va-deployment.vercel.app/ask -Method POST `
  -Headers @{"X-API-Key"="dev-key-change-me-in-production"} `
  -ContentType "application/json" `
  -Body '{"user_id":"test","question":"What is deployment?"}'
```

### Docs

https://day12-ha-tang-cloud-va-deployment.vercel.app/docs

## Environment Variables (Vercel Dashboard)

| Variable | Required | Description |
|----------|----------|-------------|
| `AGENT_API_KEY` | Yes | API key for `/ask` endpoint |
| `PLATFORM` | No | Set to `Vercel` (default in vercel.json) |
| `ENVIRONMENT` | No | `production` |
| `OPENAI_API_KEY` | No | Optional — uses mock LLM if empty |

## Local Full Stack (Docker)

See `06-lab-complete/DEPLOYMENT.md` for agent + Redis + Nginx setup.

## Screenshots

- [Vercel deployment](./screenshot/ex03.png)
