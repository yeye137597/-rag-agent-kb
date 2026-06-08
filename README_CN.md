# 智能知识库问答系统

这是一个面向学习资料、课程资料和项目文档的智能知识库问答系统。系统支持上传本地文档，构建多个独立知识库，并通过网页界面进行基于资料来源的问答。

## 功能列表

- Streamlit 网页界面
- 账号密码登录
- 用户自助注册
- 角色权限控制：管理员和普通用户
- 用户知识库授权
- 多知识库管理
- 文件上传和文本清洗
- 支持 PDF、DOCX、Markdown、TXT
- 文档解析、文本切片、向量化和索引构建
- Chroma 向量库持久化
- HuggingFace Embedding：`BAAI/bge-small-zh-v1.5`
- Chroma 向量检索 + BM25 关键词检索
- LangGraph 实现检索评估、查询改写和再检索
- DeepSeek OpenAI 兼容接口生成答案
- 答案展示引用来源
- JSONL 问答日志和 SQLite 审计日志

## 技术栈

- Python
- Streamlit
- LangChain
- LangGraph
- Chroma
- BM25
- HuggingFace Embeddings
- DeepSeek API
- SQLite
- JSONL 日志

## 安装

```bash
cd rag_agent_kb
pip install -r requirements.txt
```

首次使用 Embedding 时可能会自动下载模型。

## 配置 DeepSeek API Key

复制环境变量示例文件：

```bash
copy .env.example .env
```

然后编辑 `.env`：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

## 运行

```bash
streamlit run app.py
```

然后打开终端显示的本地地址，通常是：

```text
http://localhost:8501
```

## 默认管理员账号

系统首次启动时，如果用户表为空，会自动创建默认管理员：

```text
用户名：admin
密码：admin123
```

首次登录后请尽快修改默认管理员密码。

## 权限说明

### 管理员

管理员可以：

- 创建知识库
- 上传和清洗文件
- 构建知识库
- 删除知识库
- 查看全部知识库
- 管理用户
- 给普通用户授权知识库
- 查看审计日志和问答日志
- 对全部知识库进行问答

### 普通用户

普通用户可以：

- 自助注册账号
- 查看被授权的知识库
- 对被授权知识库进行问答
- 查看自己的问答记录

普通用户不能创建知识库、删除知识库、管理用户，也不能访问未授权知识库。

## 基本使用流程

1. 使用管理员账号登录。
2. 创建知识库。
3. 上传文档。
4. 清洗文件并预览清洗前后内容。
5. 确认是否使用清洗后的文件。
6. 构建知识库。
7. 根据需要给普通用户授权。
8. 选择知识库并提问，查看答案和引用来源。

## 问答流程

系统会先从用户选择的知识库中检索相关片段，然后判断检索内容是否足够回答问题。如果信息不足，系统会改写查询词并重新检索，最多重试两次。最终答案严格基于知识库片段生成，并展示知识库名称、文件名、页码和 chunk_id 等来源信息。

## 部署说明

这是一个 Streamlit 应用，不适合使用 GitHub Pages 部署。推荐部署到：

- Streamlit Community Cloud
- Hugging Face Spaces
- 云服务器或企业内网服务器

部署时需要在平台中配置 DeepSeek API Key。
## 模型配置说明

模型配置属于管理员功能，只有 admin 用户可以查看或修改模型配置。普通用户只能使用已配置好的模型进行知识库问答，不能修改 LLM 或 Embedding 设置。后端会强制校验管理员权限，普通 user 即使直接请求 `/api/models/config` 也会返回 403 Forbidden。

推荐使用新的环境变量：

```env
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_api_key
LLM_MODEL=deepseek-chat
LLM_TEMPERATURE=0.2

EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu

JWT_SECRET_KEY=your_jwt_secret
```

LLM 和 Embedding 是独立配置的。DeepSeek、Qwen、Kimi 等 OpenAI-compatible API 可以通过 `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` 接入。旧的 `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL` 仍然兼容，但推荐新项目使用 `LLM_*` 配置。

Embedding 当前默认使用 HuggingFace 的 `BAAI/bge-small-zh-v1.5`。切换 LLM 通常不需要重建知识库；切换 Embedding 模型通常需要重新构建知识库，因为文档向量和查询向量需要处在同一个语义向量空间。

模型设置页面不会展示 API Key 明文，只会显示是否已配置。构建知识库时会把当前 Embedding 配置写入 `metadata.json`，问答检索前会校验当前 Embedding 配置是否和知识库构建时一致。

