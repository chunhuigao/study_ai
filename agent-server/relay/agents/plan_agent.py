from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from relay.agents.base import SubAgent
from relay.schemas import PlanStep, RelayEvent, StepStatus, TaskState
from relay.state import TaskStore

Emit = Callable[[RelayEvent], Awaitable[None]]


class PlanAgent:
    """ReAct-flavored planner that coordinates domain sub-agents."""

    def __init__(self, store: TaskStore, sub_agents: list[SubAgent]) -> None:
        self.store = store
        self.sub_agents = {agent.name: agent for agent in sub_agents}

    def plan(self, user_input: str) -> list[PlanStep]:
        normalized = user_input.lower()
        steps = [
            PlanStep(
                title="澄清学习目标",
                goal="明确用户想学习的 AI 主题、当前基础和期望产出",
                agent="concept_tutor",
            ),
            PlanStep(
                title="建立知识地图",
                goal="整理概念、资料和学习路线",
                agent="researcher",
            ),
        ]
        if any(keyword in normalized for keyword in ["代码", "demo", "python", "react", "agent", "mcp"]):
            steps.append(
                PlanStep(
                    title="设计动手练习",
                    goal="设计一个能验证理解的最小实践项目",
                    agent="code_mentor",
                )
            )
        steps.append(
            PlanStep(
                title="汇总下一步",
                goal="把执行结果组织成可继续推进的学习计划",
                agent="concept_tutor",
            )
        )
        return steps

    async def run(self, task: TaskState, emit: Emit) -> TaskState:
        await emit(RelayEvent(type="task.planning", task_id=task.id, payload={"input": task.input}))
        steps = self.plan(task.input)
        self.store.set_plan(task, steps)
        await emit(
            RelayEvent(
                type="task.planned",
                task_id=task.id,
                payload={"steps": [step.model_dump(mode="json") for step in steps]},
            )
        )

        results: list[str] = []
        for step in steps:
            agent = self.sub_agents[step.agent]
            self.store.update_step(task, step.id, StepStatus.RUNNING)
            await emit(
                RelayEvent(
                    type="step.started",
                    task_id=task.id,
                    payload={"step": step.model_dump(mode="json")},
                )
            )
            try:
                result = await agent.execute(task.input, step)
                self.store.update_step(task, step.id, StepStatus.COMPLETED, result=result)
                results.append(f"## {step.title}\n{result}")
                await emit(
                    RelayEvent(
                        type="step.completed",
                        task_id=task.id,
                        payload={"step": step.model_dump(mode="json"), "result": result},
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive runtime guard
                self.store.update_step(task, step.id, StepStatus.FAILED, error=str(exc))
                self.store.fail(task, str(exc))
                await emit(
                    RelayEvent(
                        type="task.failed",
                        task_id=task.id,
                        payload={"error": str(exc), "step_id": step.id},
                    )
                )
                return task
            await asyncio.sleep(0)

        final = "\n\n".join(results)
        self.store.complete(task, final)
        await emit(RelayEvent(type="task.completed", task_id=task.id, payload={"result": final}))
        return task

