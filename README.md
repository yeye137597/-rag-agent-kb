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

