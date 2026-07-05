from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(StrEnum):
    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Skill(BaseModel):
    id: str
    name: str
    description: str = ""
    domains: list[str] = Field(default_factory=list)
    prompt: str = ""
    source: str
    path: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlanStep(BaseModel):
    id: str = Field(default_factory=lambda: f"step_{uuid4().hex[:8]}")
    title: str
    goal: str
    agent: str
    status: StepStatus = StepStatus.PENDING
    result: str | None = None
    error: str | None = None


class TaskState(BaseModel):
    id: str = Field(default_factory=lambda: f"task_{uuid4().hex[:10]}")
    input: str
    status: TaskStatus = TaskStatus.PLANNING
    steps: list[PlanStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


class TaskCreate(BaseModel):
    input: str


class RelayEvent(BaseModel):
    type: str
    task_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

