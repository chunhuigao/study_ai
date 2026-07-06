from __future__ import annotations

from pathlib import Path

from relay.agents import CodeMentorAgent, ConceptTutorAgent, PlanAgent, ResearchAgent
from relay.skills.loader import SkillLoader
from relay.state import TaskStore


def test_skill_loader_project_layer_wins(tmp_path: Path) -> None:
    project_skills = tmp_path / ".relay" / "skills"
    builtin_skills = tmp_path / "builtin"
    project_skills.mkdir(parents=True)
    builtin_skills.mkdir()

    (builtin_skills / "same.skill.json").write_text(
        """
        {
          "id": "same",
          "name": "Builtin",
          "domains": ["concept"]
        }
        """,
        encoding="utf-8",
    )
    (project_skills / "same.skill.json").write_text(
        """
        {
          "id": "same",
          "name": "Project",
          "domains": ["concept"]
        }
        """,
        encoding="utf-8",
    )

    loader = SkillLoader(
        project_root=tmp_path,
        user_home=tmp_path / "home",
        global_dir=tmp_path / "global",
        builtin_dir=builtin_skills,
    )

    assert loader.load()[0].name == "Project"


def test_plan_agent_adds_code_step_for_agent_task() -> None:
    store = TaskStore()
    planner = PlanAgent(
        store,
        [
            ConceptTutorAgent(),
            ResearchAgent(),
            CodeMentorAgent(),
        ],
    )

    plan = planner.plan("学习 AI agent，并写一个 Python demo")

    assert [step.agent for step in plan] == [
        "concept_tutor",
        "researcher",
        "code_mentor",
        "concept_tutor",
    ]

