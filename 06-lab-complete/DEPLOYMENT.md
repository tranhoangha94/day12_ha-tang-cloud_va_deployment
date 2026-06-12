# Deployment Information

## Public URL

https://day12-ha-tang-cloud-va-deployment.vercel.app

## Platform

Vercel (serverless FastAPI via Mangum)

Local full stack (Docker Compose): `06-lab-complete/` — agent × 3 + Redis + Nginx

## Test Commands

### Health Check

```bash
curl https://day12-ha-tang-cloud-va-deployment.vercel.app/health
# Expected: {"status":"ok",...}
```

Local (via Nginx load balancer):

```bash
curl http://localhost:8888/health
curl http://localhost:8888/ready
```

### API Test (with authentication)

```bash
curl -X POST https://day12-ha-tang-cloud-va-deployment.vercel.app/ask \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

Local:

```powershell
Invoke-RestMethod -Uri http://localhost:8888/ask -Method POST `
  -Headers @{"X-API-Key"="dev-key-change-me-in-production"} `
  -ContentType "application/json" `
  -Body '{"user_id":"user1","question":"What is deployment?"}'
```

## Environment Variables Set

- `PORT`
- `REDIS_URL`
- `AGENT_API_KEY`
- `RATE_LIMIT_PER_MINUTE` (10)
- `MONTHLY_BUDGET_USD` (10.0)
- `ENVIRONMENT`
- `OPENAI_API_KEY` (optional — mock LLM if empty)

## Screenshots

- [Vercel deployment](../screenshot/ex03.png)
