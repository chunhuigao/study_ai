# LangGraph Agent Web 应用

这是一个最小版 LangGraph Agent 应用，可以在 Web 浏览器中使用。后端会读取本地 `cc switch` 当前 Codex provider 的模型、base URL 和 API key，也可以用 `.env` 覆盖。

Agent 使用 LangGraph 的 `create_react_agent`，内置两个简单工具：

- `current_time`：查询指定时区的当前时间。
- `calculator`：安全计算基础四则运算表达式。

## 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 配置

如果本机已经通过 `cc switch` 配好了当前 Codex provider，可以直接运行。

也可以创建 `.env` 覆盖配置：

```bash
cp .env.example .env
```

常用覆盖项：

```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-nano
OPENAI_BASE_URL=https://api.openai.com/v1
```

## 运行 Web 应用

```bash
uvicorn web_app:app --reload --host 127.0.0.1 --port 8000
```

然后在浏览器打开：

```text
http://127.0.0.1:8000
```
