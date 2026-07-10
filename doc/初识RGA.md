# RAG（Retrieval-Augmented Generation）学习笔记

> **一句话理解：**
>
> **RAG = 检索（Retrieval）+ 增强（Augmented）+ 生成（Generation）**
>
> 即：**让大模型先查资料，再根据资料生成答案。**

---

# 目录

- 什么是 RAG
- 为什么需要 RAG
- RAG 工作流程
- RAG 核心组成
- RAG 示例
- RAG 与 Fine-tuning 的区别
- RAG 技术栈
- RAG 实现流程
- RAG 高级优化
- 总结

---

# 一、什么是 RAG

RAG（Retrieval-Augmented Generation，检索增强生成）是一种结合**信息检索（Information Retrieval）**和**大语言模型（LLM）**的 AI 技术。

传统 LLM 回答问题主要依赖训练时学习到的知识，而 RAG 在回答问题之前，会先从外部知识库中检索相关内容，再将这些内容作为上下文提供给模型，最终生成更加准确、可信的回答。

简单来说：

```text
用户提问
      │
      ▼
查询知识库
      │
      ▼
找到相关资料
      │
      ▼
将资料作为 Prompt
      │
      ▼
LLM 生成答案
```

---

# 二、为什么需要 RAG

大模型存在几个天然问题：

## 1. 知识存在截止时间

例如：

模型训练截止到：

```
2024 年 6 月
```

之后发生的事情模型并不知道。

---

## 2. 不知道企业私有数据

例如：

- 公司制度
- 内部 Wiki
- CRM 数据
- 产品文档
- API 文档

这些都没有参与模型训练。

---

## 3. 容易产生幻觉（Hallucination）

例如：

问：

> 公司有多少天年假？

模型可能会"猜"一个答案。

而 RAG 会：

```
先找到员工手册
↓

读取请假制度

↓

根据文档回答
```

因此答案更加可靠。

---

# 三、RAG 的整体流程

完整流程如下：

```text
                 用户问题
                     │
                     ▼
            Query（用户问题）
                     │
                     ▼
          Embedding（向量化）
                     │
                     ▼
      Vector Search（向量检索）
                     │
             找到相关文档
                     │
                     ▼
 Prompt = 用户问题 + 检索结果(Context)
                     │
                     ▼
                  LLM
                     │
                     ▼
                 最终答案
```

整个过程可以总结为两步：

1. 找资料
2. 根据资料回答

---

# 四、RAG 的核心组成

## 1. Documents（文档）

知识来源可以是：

- PDF
- Word
- Excel
- Markdown
- HTML
- 网页
- Notion
- Confluence
- GitHub
- 数据库
- API

例如：

```
员工手册.pdf
产品说明书.pdf
数据库文档
```

---

## 2. Chunk（文本切块）

由于大模型上下文有限，不能直接处理几百页文档。

因此需要把文档切分成多个小块。

例如：

```
1000 页 PDF

↓

Chunk1
Chunk2
Chunk3
...
Chunk1000
```

例如：

```
Chunk1
公司简介...

Chunk2
员工福利...

Chunk3
请假制度...
```

### 为什么要切块？

原因：

- Embedding 有长度限制
- 检索粒度更细
- 提高召回准确率
- 降低 Token 成本

一般 Chunk 大小：

```
200~1000 Token
```

常见：

```
300
500
800
```

---

## 3. Embedding（向量化）

Embedding 是 RAG 的核心。

它可以把文本转换成向量。

例如：

```
苹果
```

变成：

```
[0.23,0.58,-0.11,...]
```

又例如：

```
iPhone
```

变成：

```
[0.24,0.57,-0.12,...]
```

由于两个向量非常接近，因此即使用户问：

```
苹果手机
```

知识库写的是：

```
iPhone
```

依然可以检索出来。

这就是：

**语义检索（Semantic Search）**

而不是：

**关键词检索（Keyword Search）**

---

## 4. Vector Database（向量数据库）

Embedding 完成以后，需要保存。

例如：

```
Chunk1
↓

Vector1

Chunk2
↓

Vector2
```

全部保存到：

- Milvus
- FAISS
- Pinecone
- Chroma
- Weaviate
- Qdrant

用户提问：

```
怎么请假？
```

流程：

```
问题

↓

Embedding

↓

Question Vector

↓

Vector Search

↓

TopK 最相似 Chunk
```

例如：

```
Chunk18
Chunk92
Chunk103
```

---

## 5. LLM（大语言模型）

最后，把：

```
Question

+

TopK Chunk
```

一起发送给 GPT。

例如：

```
Context：

员工一年有15天年假。
连续请假超过5天需要经理审批。

Question：

公司怎么请假？
```

LLM 输出：

> 根据员工手册，公司员工每年拥有15天带薪年假，连续请假超过5天需要经理审批。

---

# 五、完整示例

知识库：

```
Chunk1

苹果是一家科技公司。
```

```
Chunk2

香蕉富含钾。
```

```
Chunk3

iPhone16 支持 AI。
```

用户提问：

```
苹果 AI 手机支持什么？
```

流程：

```
问题

↓

Embedding

↓

Vector Search

↓

找到 Chunk3

↓

Prompt

↓

LLM
```

最终回答：

```
根据知识库资料，

iPhone16 支持 AI 功能。
```

---

# 六、RAG 与 Fine-tuning 的区别

| 对比         | RAG            | Fine-tuning |
| ------------ | -------------- | ----------- |
| 修改模型参数 | ❌ 不修改      | ✅ 修改     |
| 更新知识     | 更新知识库即可 | 重新训练    |
| 企业知识     | 非常适合       | 不适合      |
| 成本         | 较低           | 较高        |
| 上线速度     | 快             | 慢          |
| 回答依据     | 外部知识       | 模型参数    |

## RAG 解决什么问题？

> 模型不知道最新知识。

## 微调解决什么问题？

> 模型不会按指定方式回答。

一句话总结：

```
RAG 解决：

知道什么（Knowledge）

Fine-tuning 解决：

怎么回答（Behavior）
```

两者可以结合使用。

---

# 七、RAG 常见技术栈

## 文档解析

- PyMuPDF
- pdfplumber
- Unstructured
- Apache Tika

---

## 文本切块

- LangChain Text Splitter
- LlamaIndex Node Parser
- RecursiveCharacterTextSplitter

---

## Embedding 模型

商业：

- OpenAI Embedding
- Voyage AI
- Jina Embeddings

开源：

- BGE
- E5
- GTE
- M3E

---

## 向量数据库

- FAISS
- Milvus
- Pinecone
- Qdrant
- Chroma
- Weaviate

---

## 检索

- Cosine Similarity
- BM25
- Hybrid Search
- Rerank

---

## 大模型

- GPT
- Claude
- Gemini
- Qwen
- DeepSeek
- Llama

---

# 八、RAG 实现流程（Python 伪代码）

```python
# 加载文档
docs = load_pdf("员工手册.pdf")

# 文本切块
chunks = split_text(docs)

# 向量化
vectors = embedding(chunks)

# 保存到向量数据库
vector_db.add(chunks, vectors)

# 用户提问
question = "公司年假多少天？"

# 问题向量化
query_vector = embedding(question)

# 检索 TopK
context = vector_db.search(query_vector, top_k=3)

# 构造 Prompt
prompt = f"""
资料：

{context}

问题：

{question}
"""

# LLM 回答
answer = llm.generate(prompt)

print(answer)
```

---

# 九、RAG 的高级优化

## 1. Hybrid Search（混合检索）

同时使用：

- BM25
- Vector Search

提高召回率。

---

## 2. Rerank（重排序）

流程：

```
先召回 Top50

↓

Rerank

↓

最终 Top5
```

这样准确率更高。

---

## 3. Query Rewrite（查询改写）

例如：

用户问：

```
苹果 AI
```

系统改写：

```
Apple iPhone AI 功能
```

检索效果更好。

---

## 4. Metadata Filter（元数据过滤）

例如：

```
部门 = HR

年份 = 2025

作者 = 张三
```

只搜索符合条件的数据。

---

## 5. Multi-hop Retrieval（多跳检索）

复杂问题需要多次检索。

例如：

```
第一步：

找到订单

↓

第二步：

找到客户

↓

第三步：

找到物流

↓

综合回答
```

---

## 6. Context Compression（上下文压缩）

由于 LLM Token 有限制。

可以：

- 摘要
- 去重
- 删除无关内容

只保留最重要的信息。

---

# 十、RAG 的优势

✅ 无需重新训练模型

✅ 企业知识实时更新

✅ 降低幻觉

✅ 支持私有数据

✅ 成本低

✅ 易于维护

---

# 十一、RAG 的局限

❌ 检索不到正确文档，回答也会出错

❌ Chunk 切分不合理，会影响检索效果

❌ Embedding 模型质量影响召回率

❌ 上下文过长会增加 Token 成本

❌ 多轮复杂推理仍然存在挑战

---

# 十二、总结

可以把 RAG 理解为：

> **RAG = 给 AI 配备了一个可以实时查阅资料的图书馆。**

整体流程如下：

```text
               文档
                 │
                 ▼
             文档解析
                 │
                 ▼
             文本切块
                 │
                 ▼
            Embedding
                 │
                 ▼
            向量数据库
                 │
      ┌──────────┴──────────┐
      │                     │
      ▼                     ▼
 用户提问              Question Embedding
      │                     │
      └──────────┬──────────┘
                 ▼
             Vector Search
                 │
          TopK 相关 Chunk
                 │
                 ▼
        Prompt（Question + Context）
                 │
                 ▼
                LLM
                 │
                 ▼
             最终生成答案
```

一句话总结：

> **RAG 并不是让模型变得更聪明，而是让模型学会"先查资料，再回答问题"。**
