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
  agent_tools.py
  zhipu_agent.py
  electron/

zhipu.py
```

- `agent-web`：React + Vite 前端。
- `agent-server`：Electron 主进程、preload 和 Python bridge。
- `agent-server/agent_tools.py`：Agent 扩展工具，包含当前时间、城市地理位置、天气查询。
- `agent-server/zhipu_agent.py`：唯一直接依赖 `zhipu.py` 的模块，负责复用模型调用、工具和解析逻辑。
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

- Python 侧需要可以导入 `zai`，并且 `zhipu.py` 中的模型调用配置可用。
- 天气和城市地理位置工具使用 Open-Meteo 公开接口，运行时需要网络访问。
- Electron 首次安装会下载桌面运行时，安装过程不能设置 `ELECTRON_SKIP_BINARY_DOWNLOAD=1`。
- 如果当前环境没有全局 `npm`，请使用本机 Node.js 自带的 npm 或 pnpm。
