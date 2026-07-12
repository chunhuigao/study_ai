from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent_app import run_agent_turn
from cc_switch_config import load_chat_model_config


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="LangGraph Agent")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


class ToolStep(BaseModel):
    name: str
    args: dict
    output: str | None = None


class AgentResponse(BaseModel):
    session_id: str
    reply: str
    steps: list[ToolStep]


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
        "tools": ["current_time", "calculator"],
    }


@app.post("/api/agent", response_model=AgentResponse)
async def agent(request: AgentRequest):
    session_id = request.session_id or str(uuid4())
    try:
        result = await run_agent_turn(request.message, session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AgentResponse(
        session_id=session_id,
        reply=result["reply"],
        steps=result["steps"],
    )
