from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class McpServerConfig:
    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


class McpRegistry:
    """A small MCP registry placeholder for Relay extensions.

    The first Relay version keeps MCP lifecycle separate from task execution.
    Sub-agents can inspect this registry and choose tools once concrete MCP
    server configs are added.
    """

    def __init__(self) -> None:
        self._servers: dict[str, McpServerConfig] = {}

    def register(self, config: McpServerConfig) -> None:
        self._servers[config.name] = config

    def list_enabled(self) -> list[McpServerConfig]:
        return [server for server in self._servers.values() if server.enabled]

    def describe_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "server": server.name,
                "command": server.command,
                "args": server.args,
                "enabled": server.enabled,
            }
            for server in self._servers.values()
        ]

