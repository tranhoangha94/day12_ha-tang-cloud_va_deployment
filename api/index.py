"""
Vercel serverless — FastAPI + Mangum (single file, Vercel chỉ bundle entrypoint).
"""
import os
import time
import random
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

# ── Mock LLM (inline — tránh import sibling modules trên Vercel) ──
MOCK_RESPONSES = {
    "default": [
        "Đây là câu trả lời từ AI agent (mock). Trong production, đây sẽ là response từ OpenAI/Anthropic.",
        "Agent đang hoạt động tốt! (mock response) Hỏi thêm câu hỏi đi nhé.",
        "Tôi là AI agent được deploy lên cloud. Câu hỏi của bạn đã được nhận.",
    ],
    "docker": ["Container là cách đóng gói app để chạy ở mọi nơi. Build once, run anywhere!"],
    "deploy": ["Deployment là quá trình đưa code từ máy bạn lên server để người khác dùng được."],
}


def mock_ask(question: str) -> str:
    time.sleep(0.1)
    q = question.lower()
    for keyword, responses in MOCK_RESPONSES.items():
        if keyword in q:
            return random.choice(responses)
    return random.choice(MOCK_RESPONSES["default"])


# ── FastAPI app ──
app = FastAPI(title="AI Agent", version="1.0.0")
START_TIME = time.time()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": f"AI Agent running on {os.getenv('PLATFORM', 'Vercel')}!",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/ask")
async def ask_agent(request: Request):
    body = await request.json()
    question = body.get("question", "")
    if not question:
        raise HTTPException(422, "question required")
    return {
        "question": question,
        "answer": mock_ask(question),
        "platform": os.getenv("PLATFORM", "Vercel"),
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "platform": os.getenv("PLATFORM", "Vercel"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


handler = Mangum(app, lifespan="off")
