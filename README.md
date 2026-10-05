# 🤖 AuraAI - Production-Grade AI Assistant & Conversational Workspace

> **MCA Major Project Documentation & Presentation Guide**
> *A full-stack, context-aware, enterprise-grade AI chat application powered by **FastAPI**, **Groq AI (GPT-OSS / LLaMA Engines)**, **MySQL**, and **Modern Responsive Web Technologies**.*

---

## 📌 Slide 1: Title & Project Overview

* **Project Title**: AuraAI - Modern Conversational AI Workspace
* **Domain**: Artificial Intelligence, Web Application Development, Cloud APIs
* **Course**: Master of Computer Applications (MCA)
* **Tech Stack**: FastAPI (Python), Groq AI (`openai/gpt-oss-120b`), MySQL Database, SQLAlchemy, Jinja2, JavaScript (SSE Streaming).

---

## 🎯 Slide 2: Abstract & Problem Statement

### Abstract

AuraAI is a high-performance, real-time AI assistant platform engineered to provide instant intelligence, seamless conversation management, file context processing, and flexible AI model integration. Built with a modular **Factory Design Pattern**, AuraAI allows instant switching between AI backends (Groq, OpenAI, Anthropic, Gemini) with zero downtime.

### Problem Statement

1. **High Latency in AI Chat Platforms**: Traditional AI applications suffer from slow response times when loading long context prompts.
2. **Provider Lock-In**: Most chat apps are tightly coupled to a single vendor (e.g. OpenAI only).
3. **Lack of Persistence & Privacy**: Free AI web interfaces often lack self-hosted database storage, context isolation, and secure enterprise user management.

---

## 🚀 Slide 3: Objectives & Key Features

* **⚡ Ultra-Fast Streaming**: Uses Server-Sent Events (SSE) to stream responses word-by-word with ultra-low latency via Groq AI.
* **🔐 Enterprise Security**: JWT authentication with bcrypt password hashing, secure HTTP cookies, and CORS controls.
* **🧱 Extensible Factory Architecture**: Easily switch between **Groq**, **OpenAI**, **Anthropic**, or **OpenRouter** dynamically via `.env` configuration.
* **💾 Persistent History**: MySQL database schema managing users, chat sessions, message logs, and uploaded context files.
* **📁 Document & File Analysis**: Upload text/code files to provide rich contextual data to the AI model.
* **🛡️ Self-Healing & Fallbacks**: Integrated fallback mechanisms to ensure 100% uptime even if external APIs experience rate limits.

---

## 🛠️ Slide 4: System Architecture & Technology Stack

```mermaid
graph TD
    User([User / Browser]) <-->|HTTP / SSE Streaming| FastAPI[FastAPI Server]
    FastAPI <-->|SQLAlchemy ORM| MySQL[(MySQL Database)]
    FastAPI <-->|Factory Pattern| AIFactory[AI Provider Factory]
    AIFactory -->|Active Provider| Groq[Groq API Engine]
    AIFactory -.->|Optional| OpenAI[OpenAI API]
    AIFactory -.->|Optional| Anthropic[Anthropic Claude API]
```

### Technology Breakdown


| Component             | Technology                   | Description                                         |
| :-------------------- | :--------------------------- | :-------------------------------------------------- |
| **Backend Framework** | **FastAPI (Python 3.11+)**   | Asynchronous, high-throughput REST API framework    |
| **AI Provider**       | **Groq LPU Engine**          | Ultra-fast inferencing running`openai/gpt-oss-120b` |
| **Database**          | **MySQL + PyMySQL**          | Relational data persistence for users & messages    |
| **ORM**               | **SQLAlchemy v2**            | Database schema modeling & query execution          |
| **Authentication**    | **PyJWT + Passlib (Bcrypt)** | Token-based security and password hashing           |
| **Frontend**          | **Jinja2 + HTML5 + CSS3**    | Dynamic responsive web UI with live stream hooks    |

---

## 🏗️ Slide 5: Software Design Patterns & Core Modules

### 1. Provider Factory Pattern (`app/ai/factory.py`)

Decouples application logic from specific AI vendors.

```python
class AIProviderFactory:
    @staticmethod
    def get_provider(provider_name=None, api_key=None):
        # Dynamically returns GroqProvider, OpenAIProvider, or AnthropicProvider
```

### 2. Multi-Model Fallback System (`app/ai/groq_provider.py`)

Ensures high availability by automatically attempting alternative models (`openai/gpt-oss-120b` ➔ `openai/gpt-oss-20b` ➔ `qwen/qwen3.8-27b`) if a primary model is busy.

---

## 🗄️ Slide 6: Database Entity-Relationship (ER) Schema

```mermaid
erDiagram
    USERS ||--o{ CONVERSATIONS : owns
    CONVERSATIONS ||--o{ MESSAGES : contains
    CONVERSATIONS ||--o{ FILES : attaches

    USERS {
        int id PK
        string email
        string hashed_password
        datetime created_at
    }

    CONVERSATIONS {
        int id PK
        int user_id FK
        string title
        datetime created_at
    }

    MESSAGES {
        int id PK
        int conversation_id FK
        string role
        text content
        datetime created_at
    }

    FILES {
        int id PK
        int conversation_id FK
        string filename
        string file_path
    }
```

---

## 🌐 Slide 7: Main API Endpoints


| Method | Endpoint             | Access    | Purpose                                         |
| :----- | :------------------- | :-------- | :---------------------------------------------- |
| `GET`  | `/api/health`        | Public    | System status, DB status, active AI model check |
| `POST` | `/api/auth/register` | Public    | Register new user account                       |
| `POST` | `/api/auth/login`    | Public    | User authentication & JWT issuance              |
| `GET`  | `/api/conversations` | Protected | Fetch user's chat history                       |
| `POST` | `/api/chat/stream`   | Protected | Real-time SSE streaming AI completions          |
| `POST` | `/api/files/upload`  | Protected | Upload document for context-aware processing    |

---

## ✅ Slide 8: Verification & Testing Results

All core backend components and external integrations have been verified:

* **Database Connection Test**: `MySQL 200 OK` (Tables initialized and active)
* **System Health Endpoint (`/api/health`)**:
  ```json
  {
    "status": "healthy",
    "app": "AuraAI",
    "environment": "development",
    "database_connected": true,
    "ai_provider": "groq",
    "ai_model": "openai/gpt-oss-120b"
  }
  ```
* **Groq AI Inference Test**: `200 OK` - Ultra-fast completion & SSE word streaming verified.

---

## ⚡ Slide 9: How to Run the Project locally

### 1. Environment Setup

Ensure your `.env` file contains your Groq API key:

```env
APP_NAME=AuraAI
ENVIRONMENT=development
PORT=8000
HOST=127.0.0.1

DATABASE_URL=mysql+pymysql://root:password@localhost:3306/aura_ai

AI_PROVIDER=groq
AI_MODEL=openai/gpt-oss-120b
```

### 2. Start Application Server

```bash
# Activate Virtual Environment
.\venv\Scripts\activate

# Run FastAPI Application
python run.py
```

* Access the Web App at: `http://127.0.0.1:8000`
* Access Swagger API Docs at: `http://127.0.0.1:8000/docs`

---

## 🔮 Slide 10: Future Enhancements & Conclusion

### Future Scope

1. **RAG Integration**: Vector embeddings using ChromaDB / FAISS for PDF document search.
2. **Multi-Modal AI**: Support for image analysis and speech-to-text input.
3. **Team Workspaces**: Shared chat sessions and role-based access control (RBAC).

### Conclusion

AuraAI successfully demonstrates a modern, scalable, context-aware AI application architecture designed to meet enterprise standards using Python, FastAPI, MySQL, and Groq's high-speed AI infrastructure.

---

*Created for MCA Project Presentation & Documentation.*
