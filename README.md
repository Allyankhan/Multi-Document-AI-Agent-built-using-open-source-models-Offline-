<div align="center">

# 📚 Multi-Document AI Agent

### 100% Local & Offline Retrieval-Augmented Generation System

*Enterprise-grade, fully decoupled RAG architecture for synthesizing answers across multiple heterogeneous documents — with zero data leakage and persistent state.*

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Async-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-ReAct%20Agent-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)](https://www.langchain.com/langgraph)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-005571?style=for-the-badge)](https://github.com/facebookresearch/faiss)
[![React](https://img.shields.io/badge/React-Vite-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

[Features](#-core-features) • [Architecture](#️-system-architecture) • [Getting Started](#-getting-started-local-development) • [Structure](#-project-structure) • [Roadmap](#-roadmap) • [Maintainer](#-maintainer)

</div>

---

## 📖 Overview

Unlike standard monolithic chat applications or API-dependent wrappers, **Multi-Document AI Agent** is engineered for **absolute privacy and offline capability**. It cleanly separates the user interface from the execution logic, combining an asynchronous Python backend, a localized vector index backed by persistent Docker volumes, and native tool-calling via local Ollama models — so no document, query, or response ever leaves your machine, and no data is lost between restarts.

At its core, it's not just RAG — it's **agentic RAG**. A LangGraph-powered ReAct agent autonomously reasons about *how* to answer a question, deciding whether to search your indexed documents, fall back to external tools, or both — with strict metadata tracking to keep multi-document answers grounded and hallucination-free.

---

## ✨ Core Features

| Feature | Description |
|---|---|
| 🔒 **100% Local Inference** | Powered entirely by local models (e.g., **Qwen 2.5:3b**, **Llama 3.2 Vision**) via Ollama — zero data leakage, fully offline. |
| 🤖 **Agentic Tool Calling (LangGraph)** | A ReAct agent graph autonomously decides when to search local documents vs. utilizing external fallback tools (e.g., web search), instead of relying on rigid, linear RAG. |
| 📚 **Multi-Document Synthesis** | Upload, index, and query multiple documents simultaneously with strict metadata tracking to prevent context hallucination and source bleed. |
| 🧩 **Decoupled Architecture** | A responsive React/Vite frontend served via Nginx, communicating with an independent, asynchronous FastAPI backend engine. |
| 🔍 **Semantic Vector Search** | Uses FAISS for localized, highly efficient L2-distance document chunk matching. |
| 🖼️ **Multimodal & OCR Support** | Utilizes `unstructured` and `rapidocr-onnxruntime` to process not just digital text, but also scanned PDFs and image files (JPEG/PNG) — paired with **Llama 3.2 Vision** for true vision-based document understanding. |
| 💾 **Persistent State Storage** | External Docker Volumes ensure FAISS indexes and uploaded files survive container restarts and redeployments — no data amnesia. |
| 🐳 **Production Containerization** | Optimized multi-stage Docker builds (Alpine + slim base images) for identical runtime environments locally and in the cloud. |
| ☁️ **Cloud-Ready CI/CD** | Automated GitHub Actions pipeline that builds, tests, and pushes production-ready images to AWS ECR. |

---

## 🏗️ System Architecture

### High-Level Component Map

| Component | Technology | Purpose |
|---|---|---|
| **Frontend UI** | React, Vite, Nginx | Seamless, non-blocking UI with stateful chat memory |
| **Backend API** | FastAPI, Python 3.11 | Asynchronous document chunking, API routing, AI orchestration |
| **Agent Engine** | LangGraph & Ollama | Autonomous decision routing (ReAct) and local token generation |
| **Vector DB** | FAISS (Persistent Volume) | Stores document embeddings for rapid semantic retrieval |
| **Infrastructure** | Docker Compose | Orchestrates network bridges and persistent volumes between decoupled microservices |

### System Architecture Flowchart

```mermaid
flowchart TD
    U["👤 User"] -->|"Uploads documents / asks question"| FE["React + Vite UI\n(served via Nginx)"]
    FE -->|"REST calls"| API["FastAPI Backend\n(Python 3.11, async)"]

    subgraph Backend["Backend Engine (Containerized)"]
        API --> ING["Document Ingestion Pipeline\n(unstructured)"]
        ING -->|"Digital text"| CHUNK["Text Chunking"]
        ING -->|"Scanned PDFs / JPEG / PNG"| OCR["OCR Extraction\n(rapidocr-onnxruntime)"]
        OCR --> CHUNK
        CHUNK --> EMB["Embedding Generation\n(Ollama)"]
        EMB --> VDB[("FAISS Vector Store\nL2 Similarity Index")]
        VDB <-.->|"read / write"| VOL[("💾 Persistent Docker Volume\nIndex + Uploaded Files")]

        API --> AGENT["LangGraph ReAct Agent"]
        AGENT -->|"Decision: search local docs"| VDB
        AGENT -->|"Decision: use fallback tool"| EXT["External Fallback Tools\n(e.g., Web Search)"]
        VDB -->|"Relevant chunks + metadata"| AGENT
        EXT -->|"Fallback results"| AGENT
        AGENT -->|"Synthesized context"| LLM["Ollama Local LLM\n(Qwen 2.5:3b / Llama 3.2 Vision)"]
        LLM -.->|"Vision-based image\n& scanned-doc reasoning"| OCR
        LLM -->|"Generated answer"| AGENT
    end

    AGENT -->|"Final response"| API
    API -->|"JSON response"| FE
    FE -->|"Rendered answer"| U

    style U fill:#4f46e5,color:#fff
    style FE fill:#61dafb,color:#000
    style API fill:#009688,color:#fff
    style AGENT fill:#1c3c3c,color:#fff
    style VDB fill:#005571,color:#fff
    style VOL fill:#f59e0b,color:#000
    style LLM fill:#111,color:#fff
    style EXT fill:#de5833,color:#fff
    style OCR fill:#7c3aed,color:#fff
```

### ReAct Agent Decision Loop (Sequence Diagram)

```mermaid
sequenceDiagram
    actor User
    participant Agent as LangGraph ReAct Agent
    participant Docs as FAISS (Local Docs)
    participant Fallback as External Fallback Tool
    participant LLM as Ollama Local LLM

    User->>Agent: Submit query
    Agent->>Agent: Reason — Can this be answered from indexed documents?

    alt Local knowledge sufficient
        Agent->>Docs: Semantic search (vector similarity)
        Docs-->>Agent: Top-k relevant chunks + source metadata
    else Local context insufficient
        Agent->>Fallback: Invoke external fallback tool
        Fallback-->>Agent: Supplementary results
    end

    Agent->>Agent: Evaluate — Is retrieved context sufficient to answer?
    alt Context sufficient
        Agent->>LLM: Synthesize context + generate answer
        LLM-->>Agent: Grounded, cited response
    else Context still insufficient
        Agent->>Fallback: Retry with alternate tool / query
        Fallback-->>Agent: Additional results
        Agent->>LLM: Re-synthesize with expanded context
        LLM-->>Agent: Final response
    end

    Agent-->>User: Deliver answer with source attribution
```

---

## 🚀 Getting Started (Local Development)

### Prerequisites

- 🐳 [Docker](https://www.docker.com/) and Docker Compose installed
- 🦙 [Ollama](https://ollama.com/) installed on your host machine, with your preferred models pulled:

```bash
ollama pull qwen2.5:3b
# optional: for multimodal / vision-based document understanding
ollama pull llama3.2-vision
```

### Installation Steps

**1. Clone the repository**

```bash
git clone https://github.com/YOUR_USERNAME/multidocument-chatbot.git
cd multidocument-chatbot
```

**2. Deploy the full stack via Docker**

```bash
docker compose up --build
```

> **Note:** `docker-compose.yml` is pre-configured to (1) route host-level Ollama traffic securely into the containerized backend, and (2) mount external volumes so the FAISS index and uploaded files persist across container restarts and redeployments.

**3. Access the application**

| Service | URL |
|---|---|
| 🖥️ Frontend UI | [http://localhost:3000](http://localhost:3000) |
| 📑 Backend API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## 📂 Project Structure

```
📦 multidocument-chatbot
 ┣ 📂 .github
 ┃ ┗ 📂 workflows
 ┃   ┗ 📜 aws-ecr-deploy.yml     # CI/CD Pipeline Configuration
 ┣ 📂 Backend
 ┃ ┣ 📂 app
 ┃ ┃ ┣ 📂 Graph                  # LangGraph ReAct Logic & Tools
 ┃ ┃ ┣ 📜 main.py                # FastAPI Entrypoint
 ┃ ┃ ┗ 📜 ...
 ┃ ┣ 📜 Dockerfile               # Python 3.11-slim Build
 ┃ ┗ 📜 requirements.txt
 ┣ 📂 frontend
 ┃ ┣ 📂 src                      # React UI Components
 ┃ ┣ 📜 Dockerfile               # Node 20-slim + Nginx Multi-stage Build
 ┃ ┗ 📜 package.json
 ┣ 📜 .gitignore                 # Environment & Database Exclusion
 ┗ 📜 docker-compose.yml         # Orchestration & Volume Config
```

---

## 🧪 Tech Stack Summary

<div align="center">

| Layer | Stack |
|---|---|
| **UI** | React · Vite · Nginx |
| **API** | FastAPI · Python 3.11 · Async I/O |
| **Orchestration** | LangGraph (ReAct Agent) |
| **LLM Runtime** | Ollama (Qwen 2.5:3b · Llama 3.2 Vision · other local models) |
| **Retrieval** | FAISS (L2 vector similarity, persistent volume) |
| **Document Parsing** | `unstructured` (multi-format ingestion) |
| **OCR Engine** | `rapidocr-onnxruntime` (scanned PDFs & images) |
| **External Tooling** | Configurable fallback tools (e.g., web search) |
| **DevOps** | Docker Compose · GitHub Actions · AWS ECR |

</div>

---

## 🗺️ Roadmap

- [ ] Support for additional local embedding models
- [ ] Hybrid persistent store (disk-backed FAISS / SQLite metadata layer)
- [ ] Multi-agent collaboration for cross-document reasoning
- [ ] Role-based access control for enterprise deployments
- [ ] Streaming token responses in the UI
- [ ] Batch OCR pre-processing queue for large scanned-document sets

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](../../issues) or open a pull request.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Maintainer

**Allyan Khan**
*Software Engineer* 

Passionate about deploying scalable agentic RAG architectures and multi-agent systems for real-world enterprise operations.

[![GitHub](https://img.shields.io/badge/GitHub-Follow-181717?style=for-the-badge&logo=github)](https://github.com/YOUR_USERNAME)

---

<div align="center">

⭐ **If you find this project useful, consider giving it a star!** ⭐

</div>
