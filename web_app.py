from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from cc_switch_config import (
    DEFAULT_SYSTEM_PROMPT,
    ai_message_to_text,
    create_chat_model,
    load_chat_model_config,
)


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="LangChain Chatbot")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

sessions: dict[str, list[Any]] = {}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class ResetRequest(BaseModel):
    session_id: str | None = None


@lru_cache(maxsize=1)
def get_chat_model():
    return create_chat_model()


def get_session_messages(session_id: str) -> list[Any]:
    if session_id not in sessions:
        sessions[session_id] = [("system", DEFAULT_SYSTEM_PROMPT)]
    return sessions[session_id]


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/config")
def get_config():
    config, _ = load_chat_model_config()
    return {
        "provider": config.provider_name,
        "model": config.model,
        "base_url": config.base_url,
        "use_responses_api": config.use_responses_api,
        "reasoning_effort": config.reasoning_effort,
        "has_api_key": config.has_api_key,
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid4())
    messages = get_session_messages(session_id)
    messages.append(("human", request.message))

    try:
        response: AIMessage = await get_chat_model().ainvoke(messages)
    except Exception as exc:
        messages.pop()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    messages.append(response)
    return ChatResponse(session_id=session_id, reply=ai_message_to_text(response))


@app.post("/api/reset")
def reset_chat(request: ResetRequest):
    if request.session_id:
        sessions.pop(request.session_id, None)
    return {"ok": True}
