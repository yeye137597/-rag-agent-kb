# Intelligent Knowledge Base QA System

An enterprise-style Retrieval-Augmented Generation (RAG) application for building and querying local knowledge bases from documents. The system supports document upload, text cleaning, knowledge base construction, multi-knowledge-base management, account login, role-based access control, and source-grounded question answering.

## Features

- Streamlit web interface
- Account login and self-registration
- Role-based access control: `admin` and `user`
- User knowledge base authorization
- Multi-knowledge-base management
- File upload and text cleaning
- Supported file types: PDF, DOCX, Markdown, TXT
- Document parsing, chunking, embedding, and indexing
- Chroma vector database persistence
- HuggingFace Embedding model: `BAAI/bge-small-zh-v1.5`
- Hybrid retrieval with Chroma vector search and BM25
- LangGraph-based retrieval evaluation and query rewriting
- DeepSeek API through an OpenAI-compatible interface
- Source citations in final answers
- JSONL query logs and SQLite audit logs

## Tech Stack

- Python
- Streamlit
- LangChain
- LangGraph
- Chroma
- BM25
- HuggingFace Embeddings
- DeepSeek API
- SQLite
- JSONL logging

## Project Structure

```text
rag_agent_kb/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
├── README_CN.md
├── data/
│   ├── app.db
│   ├── uploads/
│   ├── processed/
│   ├── chroma_db/
│   └── knowledge_bases/
├── logs/
│   └── query_logs.jsonl
└── src/
    ├── auth.py
    ├── db.py
    ├── document_loader.py
    ├── splitter.py
    ├── vector_store.py
    ├── retriever.py
    ├── llm.py
    ├── agent_graph.py
    ├── kb_manager.py
    ├── logger.py
    └── utils.py
```

Local runtime data such as `.env`, SQLite database files, uploaded documents, processed files, vector databases, and logs are excluded from Git by `.gitignore`.

## Installation

```bash
cd rag_agent_kb
pip install -r requirements.txt
```

The embedding model may be downloaded on first use.

## Environment Variables

Copy the example file:

```bash
copy .env.example .env
```

Then edit `.env`:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

## Run

```bash
streamlit run app.py
```

Open the local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## Frontend And Backend Version

The original `app.py` Streamlit application is kept as the early prototype version. The minimal separated version uses:

- `backend/`: FastAPI REST API for auth, permissions, knowledge base management, document indexing, retrieval, and LangGraph RAG question answering.
- `frontend/`: React + Vite UI for login, knowledge base selection, chat, upload, and build actions.
- `src/`: Existing RAG business logic shared by both versions.

Start the backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

Required environment variables:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
JWT_SECRET_KEY=change-this-secret
```

Default login:

```text
username: admin
password: admin123
```

FastAPI endpoints:

- `POST /api/auth/login`
- `POST /api/auth/register`
- `GET /api/auth/me`
- `GET /api/kbs`
- `POST /api/kbs`
- `POST /api/kbs/{kb_id}/upload`
- `GET /api/kbs/{kb_id}/files`
- `POST /api/kbs/{kb_id}/clean`
- `POST /api/kbs/{kb_id}/build`
- `DELETE /api/kbs/{kb_id}`
- `POST /api/chat`
- `GET /api/users`
- `POST /api/users`
- `PUT /api/users/{user_id}/active`
- `PUT /api/users/{user_id}/password`
- `PUT /api/users/{user_id}/permissions`
- `GET /api/logs/audit`
- `GET /api/logs/queries`
- `GET /api/models/config`
- `POST /api/models/config`

## Model Configuration

Model configuration is an administrator-only feature. Only `admin` users can view or modify LLM and Embedding settings. Normal `user` accounts can only use the configured models for knowledge base QA and cannot change LLM or Embedding settings. The backend enforces this with admin permission checks, so direct requests from normal users to model configuration APIs return `403 Forbidden`.

Recommended `.env` configuration:

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

LLM configuration is independent from Embedding configuration. DeepSeek, Qwen, Kimi, OpenAI, and other OpenAI-compatible APIs can be connected through `LLM_BASE_URL`, `LLM_API_KEY`, and `LLM_MODEL`. The old `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, and `DEEPSEEK_MODEL` variables remain compatible, but new deployments should prefer the `LLM_*` variables.

The model settings page never displays the API key in plain text. It only shows whether a key has been configured.

Switching the LLM usually does not require rebuilding knowledge bases. Switching the Embedding model usually requires rebuilding existing knowledge bases because document vectors and query vectors must live in the same semantic vector space. When a knowledge base is built, the current Embedding configuration is written into its `metadata.json`; chat requests validate the current Embedding configuration against that metadata before retrieval.

## Default Admin Account

On first startup, the system creates a default administrator account if no users exist:

```text
username: admin
password: admin123
```

Change the default password as soon as possible after the first login.

## Roles And Permissions

### Admin

Admins can:

- Create knowledge bases
- Upload and clean files
- Build knowledge bases
- Delete knowledge bases
- View all knowledge bases
- Manage users
- Authorize users to access knowledge bases
- View audit logs and query logs
- Ask questions across all knowledge bases

### User

Users can:

- Register a normal account
- View authorized knowledge bases
- Ask questions against authorized knowledge bases
- View their own query logs

Users cannot create knowledge bases, delete knowledge bases, manage users, or access unauthorized knowledge bases.

## Basic Workflow

1. Log in as admin.
2. Create a knowledge base.
3. Upload documents.
4. Clean files and preview the before/after content.
5. Confirm whether to use cleaned files.
6. Build the knowledge base.
7. Authorize normal users if needed.
8. Ask questions and review source citations.

## Query Flow

The system retrieves relevant chunks from the selected knowledge bases, evaluates whether the retrieved content is sufficient, rewrites the query if needed, retries retrieval up to two times, and then generates a final answer strictly based on the retrieved knowledge base content.

Final answers include source references such as knowledge base name, file name, page number, and chunk ID.

## Notes For Deployment

This is a Streamlit application and is not suitable for GitHub Pages. Recommended deployment options include:

- Streamlit Community Cloud
- Hugging Face Spaces
- A cloud server or internal company server

Configure the DeepSeek API key as a secret or environment variable on the deployment platform.
