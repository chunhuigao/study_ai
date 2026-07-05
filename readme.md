# Relay

Relay 是一个用于学习 AI 的桌面 agent。它采用 Plan-Execute 架构：Plan-Agent 以 ReAct 风格规划任务，把复杂学习目标拆成子任务，再交给专门的 sub-agent 执行。前端通过 React + Electron + TypeScript 提供安装包式界面，服务端通过 Python + AgentScope 兼容层 + WebSocket 推送任务进度。

## 架构

- `PlanAgent`：负责任务规划、协调和状态推进。
- `ConceptTutorAgent`：解释概念、生成学习问题和复盘建议。
- `ResearchAgent`：整理资料路径、官方文档和阅读顺序。
- `CodeMentorAgent`：设计最小 demo、验收方式和下一步实践。
- `SkillLoader`：按项目级、用户级、全局级、内置级四层加载 skill，前一层覆盖后一层。
- `McpRegistry`：预留 MCP server 注册与工具发现入口。

## 目录

```text
agent-server/relay/          Python agent 服务端
agent-server/relay/agents/   Plan-Agent 与 sub-agent
agent-server/relay/skills/   skill 加载机制
agent-server/relay/mcp/      MCP 扩展注册表
frontend/src/renderer/       React 界面
.relay/skills/               项目级 skill
```

## 启动

后端：

```bash
cd agent-server
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn relay.server:app --reload --host 127.0.0.1 --port 8000
```

如果要启用真正的 AgentScope runtime：

```bash
pip install -e '.[agentscope]'
```

前端：

```bash
pnpm install
pnpm dev
```

Electron：

```bash
pnpm electron:dev
```

打开界面后输入学习目标，例如：

```text
我想学习 AI agent、ReAct、MCP，并做一个 Python demo
```

Relay 会创建任务、生成计划、分派 sub-agent，并通过 WebSocket 实时显示进度。

## Skill 扩展

Relay 按顺序加载以下目录：

1. 项目级：`./.relay/skills`
2. 用户级：`~/.relay/skills`
3. 全局级：`/etc/relay/skills`，也可以用 `RELAY_GLOBAL_SKILLS` 覆盖
4. 内置级：`agent-server/relay/builtin_skills`

skill 文件使用 `*.skill.json`：

```json
{
  "id": "project.ai_agent_learning",
  "name": "Project AI Agent Learning",
  "description": "聚焦 Plan-Execute、ReAct、sub-agent、MCP 和 skill 扩展。",
  "domains": ["concept", "research", "code"],
  "prompt": "围绕 Relay 的架构目标输出学习路径和动手任务。"
}
```
