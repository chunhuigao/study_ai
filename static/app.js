const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const messages = document.querySelector("#messages");
const sendButton = document.querySelector("#send-button");
const resetButton = document.querySelector("#reset-button");

let sessionId = localStorage.getItem("langchain-chat-session-id");

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

function autoSizeInput() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

async function loadConfig() {
  const response = await fetch("/api/config");
  const config = await response.json();
  setText("#provider", config.provider);
  setText("#model", config.model);
  setText("#api-mode", config.use_responses_api ? "Responses" : "Chat Completions");

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
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "请求失败");
    }

    sessionId = data.session_id;
    localStorage.setItem("langchain-chat-session-id", sessionId);
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

resetButton.addEventListener("click", async () => {
  await fetch("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  sessionId = null;
  localStorage.removeItem("langchain-chat-session-id");
  messages.innerHTML = "";
  appendMessage("assistant", "会话已清空。");
  input.focus();
});

loadConfig().catch((error) => appendMessage("error", error.message));
autoSizeInput();
