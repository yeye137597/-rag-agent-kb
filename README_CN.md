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

