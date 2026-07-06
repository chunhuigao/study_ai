# AI RAG Learning

这是一个面向 AI 初学者的本地 RAG 学习项目。当前版本只支持上传 PDF，后续可以沿用同一条数据链路扩展到视频、网页、Markdown 等资料类型。

## RAG 流程

```text
上传 PDF
  -> Python 抽取文本
  -> 文本切成 chunk
  -> 保存本地索引
  -> 用户提问
  -> 检索相关 chunk
  -> 返回回答草稿和引用片段
```

当前实现刻意保持简单，没有引入向量数据库，也没有强依赖大模型。检索使用轻量关键词打分，方便学习 RAG 的完整骨架。

## 启动

安装前端依赖：

```bash
pnpm install
```

安装 PDF 解析依赖：

```bash
pnpm setup:python
```

启动桌面应用：

```bash
pnpm start
```

## 核心文件

- `agent-server/python/agent_server/rag.py`：PDF 抽取、切块、索引、检索、回答。
- `agent-server/python/agent_server/bridge.py`：Electron 调 Python 的命令入口。
- `agent-server/electron/main.js`：Electron 主进程和 IPC。
- `agent-server/electron/preload.cjs`：暴露安全的 `window.ragApi`。
- `agent-web/src/App.jsx`：RAG 上传和问答界面。

## 后续扩展视频

视频资料可以新增一个 ingestion 函数：

1. 用音视频工具抽取音频。
2. 用语音识别把音频转文字。
3. 复用 `rag.py` 里的切块、保存索引、检索和问答逻辑。

