# 智能知识库问答系统

这是一个基于 Streamlit、LangChain、LangGraph、Chroma、BM25 和 DeepSeek API 的本地知识库问答 MVP。你可以上传 PDF、Word、Markdown、txt 等学习资料或项目文档，系统会解析、切片、向量化并持久化到 Chroma，然后通过网页界面进行基于资料来源的问答。

## 功能列表

- Streamlit 网页界面，支持多文件上传和在线提问
- 支持 PDF、docx、md、txt 文档解析
- 使用 `RecursiveCharacterTextSplitter` 进行中文友好的文本切片
- 使用 `BAAI/bge-small-zh-v1.5` 生成 HuggingFace Embedding
- 使用 Chroma 持久化向量库，目录为 `data/chroma_db`
- 使用 Chroma 向量检索和 BM25 关键词检索做混合检索
- 使用 LangGraph 实现检索评估、查询改写、再检索和最终回答
- 使用 DeepSeek OpenAI 兼容接口生成评估结果和答案
- 答案展示来源文件名、页码和片段 ID
- 每次问答写入 `logs/query_logs.jsonl`

## 技术栈

- Python
- Streamlit
- LangChain
- LangGraph
- Chroma
- BM25
- HuggingFace Embedding: `BAAI/bge-small-zh-v1.5`
- DeepSeek API: OpenAI 兼容接口
- JSONL 日志

## 安装步骤

```bash
cd rag_agent_kb
pip install -r requirements.txt
```

首次运行会下载 Embedding 模型，耗时取决于网络和机器性能。

## 配置 DeepSeek API Key

复制环境变量示例文件：

```bash
copy .env.example .env
```

然后编辑 `.env`：

```env
DEEPSEEK_API_KEY=你的 DeepSeek API Key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

## 如何运行

```bash
streamlit run app.py
```

打开终端显示的本地地址，例如 `http://localhost:8501`。

## 如何上传文档

1. 在左侧栏点击上传文件。
2. 选择一个或多个 PDF、docx、md、txt 文件。
3. 点击“构建知识库”。
4. 系统会保存文件到 `data/uploads`，解析后写入 `data/chroma_db`。

## 如何提问

1. 在页面中间的问题输入框输入问题。
2. 点击“生成答案”。
3. 系统会先进行混合检索，再由 LangGraph Agent 判断资料是否足够。
4. 如果资料不足，Agent 会改写查询词并最多重试 2 次。
5. 最终答案会展示引用来源。

## 项目亮点

- 结构清晰：页面、加载、切片、检索、LLM、Agent、日志各自独立
- 支持混合检索：结合语义向量检索和 BM25 关键词检索
- Agent 化流程：通过 LangGraph 实现评估、改写、再检索
- 可追溯：答案和日志都保留来源文件、页码、片段 ID
- 可扩展：后续可以加入用户权限、增量索引、重排序、对话记忆和在线文档同步

## 面试介绍话术

这个项目是一个面向个人学习资料和项目文档的智能知识库问答系统。我使用 Streamlit 构建前端交互，用 LangChain 完成文档加载、切片、Embedding 和检索，用 Chroma 持久化向量库，并结合 BM25 做混合检索，提升中文资料中关键词和语义召回的稳定性。

在生成答案前，我用 LangGraph 设计了一个简单 Agent 流程：先检索，再让 LLM 判断资料是否足够，如果不足则改写查询词并重新检索，最多重试 2 次。最终回答严格要求基于知识库片段，并输出文件名、页码和 chunk_id，避免模型脱离资料编造内容。

此外，系统会把每次查询写入 JSONL 日志，包括原始问题、改写问题、召回片段、答案、耗时和评估原因，方便后续做效果分析、召回优化和面试展示。

