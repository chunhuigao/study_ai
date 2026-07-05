from __future__ import annotations

from relay.agents.base import SubAgent
from relay.schemas import PlanStep


class ConceptTutorAgent(SubAgent):
    name = "concept_tutor"
    domain = "concept"

    async def execute(self, user_input: str, step: PlanStep) -> str:
        return (
            f"概念学习建议：围绕「{step.goal}」先建立直觉，再补定义和反例。\n"
            "推荐输出：核心概念卡片、3 个检查问题、1 个小练习。\n\n"
            f"可用 skill：\n{self.skill_context()}"
        )


class ResearchAgent(SubAgent):
    name = "researcher"
    domain = "research"

    async def execute(self, user_input: str, step: PlanStep) -> str:
        return (
            f"资料整理建议：为「{step.goal}」收集官方文档、经典论文、实践案例，并标注适用边界。\n"
            "推荐输出：阅读顺序、每份资料的用途、需要跳过的噪音。\n\n"
            f"可用 skill：\n{self.skill_context()}"
        )


class CodeMentorAgent(SubAgent):
    name = "code_mentor"
    domain = "code"

    async def execute(self, user_input: str, step: PlanStep) -> str:
        return (
            f"动手实践建议：把「{step.goal}」拆成一个可运行 demo，再逐步加入评估和日志。\n"
            "推荐输出：最小代码任务、验收方式、下一步重构点。\n\n"
            f"可用 skill：\n{self.skill_context()}"
        )

