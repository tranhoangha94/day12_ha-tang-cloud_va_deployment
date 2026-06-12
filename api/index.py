"""
Vercel serverless — FastAPI (export `app` trực tiếp, không dùng Mangum).

Vercel Python runtime hỗ trợ ASGI native; Mangum + Python 3.12 gây 500 FUNCTION_INVOCATION_FAILED.
"""
import os
import time
import random
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

MOCK_RESPONSES = {
    "default": [
        "Day la cau tra loi tu AI agent (mock). Trong production, day se la response tu OpenAI.",
        "Agent dang hoat dong tot! (mock response)",
        "Toi la AI agent duoc deploy len Vercel. Cau hoi cua ban da duoc nhan.",
    ],
    "docker": ["Container la cach dong goi app de chay o moi noi. Build once, run anywhere!"],
    "deploy": ["Deployment la qua trinh dua code tu may ban len server de nguoi khac dung duoc."],
}

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
AGENT_API_KEY = os.getenv("AGENT_API_KEY", "dev-key-change-me-in-production")

app = FastAPI(
    title="AI Agent",
    version="1.0.0",
    description="Day 12 Lab — Cloud deployment on Vercel",
)
START_TIME = time.time()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def mock_ask(question: str) -> str:
    q = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in q:
            return random.choice(responses)
    return random.choice(MOCK_RESPONSES["default"])


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    if api_key != AGENT_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(default="default", max_length=64)


@app.get("/")
def root():
    return {
        "message": f"AI Agent running on {os.getenv('PLATFORM', 'Vercel')}!",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "platform": os.getenv("PLATFORM", "Vercel"),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/ready")
def ready():
    return {"ready": True}


@app.post("/ask")
async def ask_agent(body: AskRequest, _key: str = Depends(verify_api_key)):
    return {
        "question": body.question,
        "answer": mock_ask(body.question),
        "user_id": body.user_id,
        "platform": os.getenv("PLATFORM", "Vercel"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
