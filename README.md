# PDF RAG Chatbot

一个可以上传 PDF、抽取多栏文本、扫描件 OCR、切块入库到 ChromaDB，并通过聊天接口召回回答的小型 RAG 应用。

## 功能

- PDF 上传和持久化
- 基于 PyMuPDF 的文本块抽取和双栏排序
- 扫描页自动尝试 OCR
- ChromaDB 本地向量库持久化
- OpenAI embedding/chat 模式
- 无 `OPENAI_API_KEY` 时使用本地哈希向量和原文片段兜底

## 安装

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

扫描件 OCR 需要系统安装 Tesseract：

```bash
brew install tesseract tesseract-lang
```

中文扫描件建议保留默认：

```bash
export OCR_LANGUAGE=eng+chi_sim
```

如果 `tesseract` 不在系统 `PATH` 中，可以显式指定路径：

```bash
export TESSERACT_CMD=/usr/local/bin/tesseract
```

## 启动

```bash
export OPENAI_API_KEY=你的_key
uvicorn app.main:app --reload
```

浏览器打开：

```text
http://127.0.0.1:8000
```

## 常用配置

```bash
export CHROMA_COLLECTION=pdf_documents
export EMBEDDING_MODEL=text-embedding-3-small
export CHAT_MODEL=gpt-4o-mini
export CHUNK_SIZE=900
export CHUNK_OVERLAP=160
export TOP_K=6
export OCR_DPI=220
```

## API

上传 PDF：

```bash
curl -F "file=@paper.pdf" http://127.0.0.1:8000/api/upload
```

聊天：

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"这篇文档的核心结论是什么？","top_k":6}'
```

查看索引状态：

```bash
curl http://127.0.0.1:8000/api/stats
```

## 说明

数据默认保存在 `data/`：

- `data/uploads/`：上传的 PDF
- `data/chroma/`：ChromaDB 持久化索引

如果没有设置 `OPENAI_API_KEY`，应用仍可上传和召回，但回答会退化为相关片段摘取；设置 key 后会使用语义 embedding 和聊天模型生成答案。
