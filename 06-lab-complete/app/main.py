"""
Production AI Agent — Kết hợp tất cả Day 12 concepts (Part 6)

Checklist:
  ✅ Config từ environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication (auth.py)
  ✅ Redis rate limiting (rate_limiter.py)
  ✅ Redis cost guard (cost_guard.py)
  ✅ Conversation history trong Redis (session.py)
  ✅ Health check + Readiness probe (Redis ping)
  ✅ Graceful shutdown
  ✅ Security headers + CORS
"""
import json
import logging
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.auth import verify_api_key
from app.config import settings
from app.cost_guard import check_budget, record_usage
from app.rate_limiter import check_rate_limit
from app.redis_client import ping_redis
from app.session import get_history, save_turn
from utils.mock_llm import ask as llm_ask

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    if not ping_redis():
        logger.error(json.dumps({"event": "redis_unavailable"}))
    else:
        _is_ready = True
        logger.info(json.dumps({"event": "ready"}))

    yield

    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    try:
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if "server" in response.headers:
            del response.headers["server"]
        duration = round((time.time() - start) * 1000, 1)
        logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "ms": duration,
        }))
        return response
    except Exception:
        _error_count += 1
        raise


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="default", min_length=1, max_length=64)


class AskResponse(BaseModel):
    question: str
    answer: str
    model: str
    user_id: str
    history_turns: int
    timestamp: str


@app.get("/", tags=["Info"])
def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key)",
            "health": "GET /health",
            "ready": "GET /ready",
        },
    }


@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask_agent(
    body: AskRequest,
    request: Request,
    _key: str = Depends(verify_api_key),
):
    check_rate_limit(body.user_id)
    check_budget(body.user_id)

    history = get_history(body.user_id)
    input_tokens = len(body.question.split()) * 2

    logger.info(json.dumps({
        "event": "agent_call",
        "user_id": body.user_id,
        "q_len": len(body.question),
        "history_turns": len(history),
        "client": str(request.client.host) if request.client else "unknown",
    }))

    # Context từ history (mock LLM vẫn dùng question hiện tại)
    if history:
        context_hint = history[-1].get("answer", "")[:100]
        question = f"[context: {context_hint}] {body.question}"
    else:
        question = body.question

    answer = llm_ask(question)
    output_tokens = len(answer.split()) * 2
    record_usage(body.user_id, input_tokens, output_tokens)
    save_turn(body.user_id, body.question, answer)

    return AskResponse(
        question=body.question,
        answer=answer,
        model=settings.llm_model,
        user_id=body.user_id,
        history_turns=len(history) + 1,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/health", tags=["Operations"])
def health():
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "checks": {
            "llm": "openai" if settings.openai_api_key else "mock",
            "redis": "ok" if ping_redis() else "down",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready", tags=["Operations"])
def ready():
    if not _is_ready or not ping_redis():
        raise HTTPException(503, "Not ready")
    return {"ready": True}


@app.get("/metrics", tags=["Operations"])
def metrics(_key: str = Depends(verify_api_key)):
    from app.redis_client import get_redis

    r = get_redis()
    global_cost = float(r.get(f"cost:global:{time.strftime('%Y-%m')}") or 0)
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "monthly_budget_usd": settings.monthly_budget_usd,
        "global_cost_usd": round(global_cost, 4),
    }


def _handle_signal(signum, _frame):
    logger.info(json.dumps({"event": "signal", "signum": signum}))


signal.signal(signal.SIGTERM, _handle_signal)


if __name__ == "__main__":
    logger.info("Starting %s on %s:%s", settings.app_name, settings.host, settings.port)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
    )
