# Electron Agent

一个最简 Electron + React Agent 示例。前端负责多轮对话 UI 和执行轨迹展示，服务端侧负责 Electron IPC 与 Python Agent 桥接。

## 目录结构

```text
agent-web/
  index.html
  src/
  vite.config.js

agent-server/
  agent_bridge.py
  config/
  electron/
  python/
    agent_server/
      bridge.py
      model_config.py
      zhipu_agent.py
      tools/
  var/

package.json
zhipu.py
```

- `agent-web`：React + Vite 前端。
- `agent-server/electron`：Electron 主进程和 preload。
- `agent-server/agent_bridge.py`：Electron 调用 Python 的稳定入口。
- `agent-server/python/agent_server/bridge.py`：JSON stdin/stdout 协议层。
- `agent-server/python/agent_server/zhipu_agent.py`：Agent 主循环、模型调用和工具调度。
- `agent-server/python/agent_server/tools`：Agent 扩展工具，包含当前时间、城市地理位置、天气和联网搜索。
- `agent-server/python/agent_server/skills.py`：Skill 注册与配置层，负责内置 skill 和配置 skill 的加载、启停和工具暴露。
- `agent-server/config`：模型配置目录，复制 `model_config.example.json` 为 `model_config.json` 后填写本地配置。
- `agent-server/var/logs`：运行日志目录，不提交到版本库。
- `dist`：前端构建产物目录，由构建命令生成，不提交到版本库。
- `zhipu.py`：保留在项目根目录，不在本项目分层调整中修改。

## 运行

```bash
npm install
npm start
```

如果本机使用 pnpm：

```bash
pnpm install
pnpm start
```

运行前提：

- Python 侧需要可以导入 `zai`。
- 需要配置 `agent-server/config/model_config.json`，可从 `agent-server/config/model_config.example.json` 复制。
- 可选配置 `agent-server/config/skills.json`，可从 `agent-server/config/skills.example.json` 复制；也可以在应用右侧 Skills 面板中新增和启停 skill。
- 天气和城市地理位置工具使用 Open-Meteo 公开接口，运行时需要网络访问。
- Electron 首次安装会下载桌面运行时，安装过程不能设置 `ELECTRON_SKIP_BINARY_DOWNLOAD=1`。
- 如果当前环境没有全局 `npm`，请使用本机 Node.js 自带的 npm 或 pnpm。
