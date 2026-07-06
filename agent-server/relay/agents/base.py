from __future__ import annotations

from abc import ABC, abstractmethod

from relay.schemas import PlanStep, Skill


class SubAgent(ABC):
    name: str
    domain: str

    def __init__(self, skills: list[Skill] | None = None) -> None:
        self.skills = skills or []

    @abstractmethod
    async def execute(self, user_input: str, step: PlanStep) -> str:
        raise NotImplementedError

    def skill_context(self) -> str:
        if not self.skills:
            return "No matching custom skills were loaded."
        return "\n".join(f"- {skill.name}: {skill.description}" for skill in self.skills)

