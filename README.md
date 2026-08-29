# AI-Powered Resume Intelligence Platform

A containerized, full-stack Applicant Tracking System (ATS) that leverages a custom Two-Pass LLM architecture and hybrid vector search to perform highly accurate, evidence-backed candidate matching.

Traditional ATS platforms rely on rigid keyword matching, leading to "keyword stuffing" exploits and missed talent. This platform solves that by utilizing a domain-agnostic, multi-layered AI pipeline that extracts literal skills, infers semantic proficiencies, and ranks candidates against job descriptions using 384-dimensional vector embeddings.

## 🚀 Key Features

* **Two-Pass LLM Extraction Pipeline:** Separates literal data scanning from semantic inference using Gemini 3.6 Flash. This mitigates LLM cognitive load and hallucination, generating evidence-backed proficiency scores (1–5) and neutralizing ATS keyword-stuffing exploits.
* **Domain-Agnostic Semantic Ranking:** Evaluates resumes across any industry by dynamically aligning candidate capabilities against LLM-extracted job priorities using ChromaDB vector retrieval (`all-MiniLM-L6-v2`) and a custom weighted scoring matrix.
* **Production-Grade Infrastructure:** Fully containerized with Docker Compose, integrating a FastAPI/PostgreSQL backend with a Streamlit frontend and seamless Alembic schema migrations across isolated database volumes.
* **Security & Reliability:** Implements strict JSON-schema constraints, prompt-level injection mitigation for untrusted PDF inputs, and deterministic regex fallbacks for PII extraction.
* **Highly Optimized Backend:** Profiled under 50 concurrent threads using `py-spy`. Diagnosed and resolved PostgreSQL connection-pool starvation to improve throughput by ~35% (21 → 28.5 RPS avg) while maintaining ~65ms single-request latency.

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **Backend:** FastAPI, Python, Uvicorn
* **Database & ORM:** PostgreSQL, SQLAlchemy, Alembic (Migrations)
* **AI & NLP:** Google Gemini 3.6 Flash, Sentence Transformers
* **Vector Store:** ChromaDB
* **DevOps & Profiling:** Docker, Docker Compose, py-spy

## 🚦 Getting Started

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* A [Google Gemini API Key](https://aistudio.google.com/).

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git)
cd YOUR_REPOSITORY_NAME
