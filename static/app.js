const form = document.querySelector("#agent-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const resetButton = document.querySelector("#reset-button");

let sessionId = localStorage.getItem("langgraph-agent-session-id");

function setText(id, value) {
  document.querySelector(id).textContent = value || "未配置";
}

function appendMessage(role, text) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  article.appendChild(bubble);
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
}

function appendToolStep(step) {
  const args = JSON.stringify(step.args, null, 2);
  const output = step.output || "工具没有返回内容";
  appendMessage("tool", `工具：${step.name}\n参数：${args}\n结果：${output}`);
}

function autoSizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

async function loadConfig() {
  const response = await fetch("/api/config");
  const config = await response.json();

  setText("#provider", config.provider);
  setText("#model", config.model);
  setText("#tools", (config.tools || []).join(", "));

  if (!config.has_api_key) {
    appendMessage("error", "没有找到 API key。请检查 .env、环境变量或 cc switch 当前 provider 配置。");
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  appendMessage("user", text);
  input.value = "";
  autoSizeInput();
  sendButton.disabled = true;

  try {
    const response = await fetch("/api/agent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "请求失败");
    }

    sessionId = data.session_id;
    localStorage.setItem("langgraph-agent-session-id", sessionId);
    for (const step of data.steps || []) {
      appendToolStep(step);
    }
    appendMessage("assistant", data.reply);
  } catch (error) {
    appendMessage("error", error.message);
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
});

input.addEventListener("input", autoSizeInput);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

resetButton.addEventListener("click", () => {
  sessionId = null;
  localStorage.removeItem("langgraph-agent-session-id");
  messages.innerHTML = "";
  appendMessage("assistant", "已开始新会话。");
  input.focus();
});

loadConfig().catch((error) => appendMessage("error", error.message));
autoSizeInput();
