# LangChain 简单聊天机器人

这是一个最小版 LangChain 聊天机器人，支持命令行和 Web 浏览器。默认会读取本地 `cc switch` 当前 Codex provider 的模型、base URL 和 API key，也可以用 `.env` 覆盖。

## 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置环境变量

```bash
cp .env.example .env
```

如果本地 `cc switch` 已经配置了当前 Codex provider，可以不创建 `.env`。也可以编辑 `.env` 覆盖配置：

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano
OPENAI_BASE_URL=https://api.openai.com/v1
```

支持的覆盖项包括 `OPENAI_API_KEY`、`OPENAI_MODEL`、`OPENAI_BASE_URL`、`OPENAI_WIRE_API`、`OPENAI_REASONING_EFFORT` 和 `OPENAI_TEMPERATURE`。

## 命令行运行

```bash
python3 chatbot.py
```

输入 `exit` 或 `quit` 退出聊天。

## Web 端运行

```bash
uvicorn web_app:app --reload --host 127.0.0.1 --port 8888
```

然后在浏览器打开：

```text
http://127.0.0.1:8000
```
