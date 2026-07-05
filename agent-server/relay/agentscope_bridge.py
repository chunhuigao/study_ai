from __future__ import annotations

from dataclasses import dataclass
from importlib.util import find_spec


@dataclass(frozen=True)
class AgentScopeRuntime:
    available: bool
    version_hint: str
    note: str


def inspect_agentscope() -> AgentScopeRuntime:
    if find_spec("agentscope") is None:
        return AgentScopeRuntime(
            available=False,
            version_hint="not installed",
            note="Install the server dependencies to enable AgentScope-backed agents.",
        )
    return AgentScopeRuntime(
        available=True,
        version_hint="installed",
        note="Relay can wrap AgentScope agents through this bridge.",
    )

