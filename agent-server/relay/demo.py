from __future__ import annotations

import asyncio

from relay.agents import CodeMentorAgent, ConceptTutorAgent, PlanAgent, ResearchAgent
from relay.schemas import RelayEvent
from relay.skills.loader import SkillLoader
from relay.state import TaskStore
from relay.server import PROJECT_ROOT


async def main() -> None:
    store = TaskStore()
    loader = SkillLoader(project_root=PROJECT_ROOT)
    planner = PlanAgent(
        store,
        [
            ConceptTutorAgent(loader.match("concept")),
            ResearchAgent(loader.match("research")),
            CodeMentorAgent(loader.match("code")),
        ],
    )
    task = store.create("我想学习 AI agent、ReAct、MCP，并做一个 Python demo")

    async def emit(event: RelayEvent) -> None:
        print(event.model_dump_json())

    await planner.run(task, emit)
    print(task.result)


if __name__ == "__main__":
    asyncio.run(main())

