const uploadForm = document.querySelector("#uploadForm");
const pdfInput = document.querySelector("#pdfInput");
const fileLabel = document.querySelector("#fileLabel");
const uploadButton = document.querySelector("#uploadButton");
const runtimeMode = document.querySelector("#runtimeMode");
const chunkCount = document.querySelector("#chunkCount");
const docCount = document.querySelector("#docCount");
const documentList = document.querySelector("#documentList");
const chatForm = document.querySelector("#chatForm");
const questionInput = document.querySelector("#questionInput");
const topK = document.querySelector("#topK");
const sendButton = document.querySelector("#sendButton");
const messages = document.querySelector("#messages");

pdfInput.addEventListener("change", () => {
  fileLabel.textContent = pdfInput.files[0]?.name || "选择 PDF";
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = pdfInput.files[0];
  if (!file) {
    addMessage("system", "请选择一个 PDF 文件。");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  uploadButton.disabled = true;
  uploadButton.textContent = "处理中";

  try {
    const result = await request("/api/upload", {
      method: "POST",
      body: formData,
    });
    const uploadSummary = `已入库 ${result.filename}：${result.pages} 页，${result.chunks} 个 chunks，文本 ${result.text_pages} 页，OCR ${result.ocr_pages} 页，空文本 ${result.empty_pages} 页。`;
    addMessage("system", result.warning ? `${uploadSummary}\n\n${result.warning}` : uploadSummary);
    pdfInput.value = "";
    fileLabel.textContent = "选择 PDF";
    await loadStats();
  } catch (error) {
    addMessage("error", error.message);
  } finally {
    uploadButton.disabled = false;
    uploadButton.textContent = "上传并入库";
  }
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (!question) return;

  addMessage("user", question);
  questionInput.value = "";
  sendButton.disabled = true;

  try {
    const result = await request("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, top_k: Number(topK.value) }),
    });
    addMessage("assistant", result.answer, result.sources);
  } catch (error) {
    addMessage("error", error.message);
  } finally {
    sendButton.disabled = false;
    questionInput.focus();
  }
});

async function request(url, options = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) {
    const detail = typeof payload === "object" ? payload.detail : payload;
    throw new Error(detail || "请求失败");
  }
  return payload;
}

async function loadStats() {
  const stats = await request("/api/stats");
  chunkCount.textContent = stats.chunks;
  docCount.textContent = stats.documents.length;
  runtimeMode.textContent = `${stats.embedding} embeddings · ${stats.chat} chat`;
  documentList.innerHTML = "";

  if (!stats.documents.length) {
    const empty = document.createElement("div");
    empty.className = "doc-row";
    empty.innerHTML = "<strong>等待 PDF</strong><span>知识库为空</span>";
    documentList.append(empty);
    return;
  }

  for (const indexedDocument of stats.documents) {
    const row = document.createElement("div");
    row.className = "doc-row";
    const extraction = indexedDocument.extractions.join(", ") || "text";
    row.innerHTML = `
      <strong>${escapeHtml(indexedDocument.source)}</strong>
      <span>${indexedDocument.pages} 页 · ${escapeHtml(extraction)}</span>
    `;
    documentList.append(row);
  }
}

function addMessage(role, text, sources = []) {
  const item = document.createElement("article");
  item.className = `message ${role}`;

  const body = document.createElement("p");
  body.textContent = text;
  item.append(body);

  if (sources?.length) {
    const sourceList = document.createElement("div");
    sourceList.className = "sources";
    for (const source of sources) {
      const sourceItem = document.createElement("div");
      sourceItem.className = "source";
      sourceItem.textContent = `${source.source} · page ${source.page} · score ${source.score}: ${source.preview}`;
      sourceList.append(sourceItem);
    }
    item.append(sourceList);
  }

  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadStats().catch((error) => {
  runtimeMode.textContent = "状态读取失败";
  addMessage("error", error.message);
});
