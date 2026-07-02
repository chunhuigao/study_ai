# Electron Agent

一个最简 Electron + React Agent 示例。Electron 主进程通过 `agent_bridge.py` 调用现有的 `zhipu.py`，前端负责多轮对话 UI 和执行轨迹展示。

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
- Electron 首次安装会下载桌面运行时，安装过程不能设置 `ELECTRON_SKIP_BINARY_DOWNLOAD=1`。
- 如果当前环境没有全局 `npm`，请使用本机 Node.js 自带的 npm 或 pnpm。
