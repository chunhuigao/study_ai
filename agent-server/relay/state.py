from __future__ import annotations

from collections.abc import Callable

from relay.schemas import PlanStep, RelayEvent, StepStatus, TaskState, TaskStatus

EventSink = Callable[[RelayEvent], None]


class TaskStore:
    def __init__(self) -> None:
        self._tasks: dict[str, TaskState] = {}

    def create(self, user_input: str) -> TaskState:
        task = TaskState(input=user_input)
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> TaskState | None:
        return self._tasks.get(task_id)

    def list(self) -> list[TaskState]:
        return sorted(self._tasks.values(), key=lambda task: task.created_at, reverse=True)

    def set_plan(self, task: TaskState, steps: list[PlanStep]) -> None:
        task.steps = steps
        task.status = TaskStatus.RUNNING
        task.touch()

    def update_step(
        self,
        task: TaskState,
        step_id: str,
        status: StepStatus,
        result: str | None = None,
        error: str | None = None,
    ) -> None:
        for step in task.steps:
            if step.id == step_id:
                step.status = status
                step.result = result if result is not None else step.result
                step.error = error if error is not None else step.error
                task.touch()
                return
        raise KeyError(f"Unknown step id: {step_id}")

    def complete(self, task: TaskState, result: str) -> None:
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.touch()

    def fail(self, task: TaskState, error: str) -> None:
        task.status = TaskStatus.FAILED
        task.result = error
        task.touch()

    def record_event(self, task: TaskState, event: RelayEvent) -> None:
        task.events.append(event.model_dump(mode="json"))
        task.touch()

