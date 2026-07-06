from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from relay.agents import CodeMentorAgent, ConceptTutorAgent, PlanAgent, ResearchAgent
from relay.agentscope_bridge import inspect_agentscope
from relay.mcp.registry import McpRegistry, McpServerConfig
from relay.schemas import RelayEvent, TaskCreate
from relay.skills.loader import SkillLoader
from relay.state import TaskStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]

store = TaskStore()
skill_loader = SkillLoader(project_root=PROJECT_ROOT)
mcp_registry = McpRegistry()
mcp_registry.register(McpServerConfig(name="filesystem", command="npx", args=["-y", "@modelcontextprotocol/server-filesystem"]))


def build_planner() -> PlanAgent:
    return PlanAgent(
        store=store,
        sub_agents=[
            ConceptTutorAgent(skill_loader.match("concept")),
            ResearchAgent(skill_loader.match("research")),
            CodeMentorAgent(skill_loader.match("code")),
        ],
    )


app = FastAPI(title="Relay Agent Server", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, Any]:
    runtime = inspect_agentscope()
    return {
        "ok": True,
        "name": "Relay",
        "agentscope": runtime.__dict__,
        "skills": [skill.model_dump(mode="json") for skill in skill_loader.load()],
        "mcp": mcp_registry.describe_tools(),
    }


@app.get("/tasks")
async def list_tasks() -> list[dict[str, Any]]:
    return [task.model_dump(mode="json") for task in store.list()]


@app.post("/tasks")
async def create_task(payload: TaskCreate) -> dict[str, Any]:
    task = store.create(payload.input)

    async def ignore_emit(event: RelayEvent) -> None:
        store.record_event(task, event)

    await build_planner().run(task, ignore_emit)
    return task.model_dump(mode="json")


@app.websocket("/ws")
async def websocket_tasks(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            if message.get("type") != "task.create":
                await websocket.send_json({"type": "error", "payload": {"error": "Unsupported message type"}})
                continue
            payload = TaskCreate(input=message.get("input", ""))
            task = store.create(payload.input)

            async def emit(event: RelayEvent) -> None:
                store.record_event(task, event)
                await websocket.send_json(event.model_dump(mode="json"))

            await emit(RelayEvent(type="task.created", task_id=task.id, payload=task.model_dump(mode="json")))
            asyncio.create_task(build_planner().run(task, emit))
    except WebSocketDisconnect:
        return

