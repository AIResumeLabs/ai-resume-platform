# AI-Powered Resume Intelligence Platform

A containerized, full-stack Applicant Tracking System (ATS) that leverages a custom Two-Pass LLM architecture and hybrid vector search to perform highly accurate, evidence-backed candidate matching.

Traditional ATS platforms rely on rigid keyword matching, leading to "keyword stuffing" exploits and missed talent. This platform solves that by utilizing a domain-agnostic, multi-layered AI pipeline that extracts literal skills, infers semantic proficiencies, and ranks candidates against job descriptions using 384-dimensional vector embeddings.

## 🚀 Key Features

* **Two-Pass LLM Extraction Pipeline:** Separates literal data scanning from semantic inference using Gemini 2.5 Flash. This mitigates LLM cognitive load and hallucination, generating evidence-backed proficiency scores (1–5) and neutralizing ATS keyword-stuffing exploits.
* **Domain-Agnostic Semantic Ranking:** Evaluates resumes across any industry by dynamically aligning candidate capabilities against LLM-extracted job priorities using ChromaDB vector retrieval (`all-MiniLM-L6-v2`) and a custom weighted scoring matrix.
* **Production-Grade Infrastructure:** Fully containerized with Docker Compose, integrating a FastAPI/PostgreSQL backend with a Streamlit frontend and seamless Alembic schema migrations across isolated database volumes.
* **Security & Reliability:** Implements strict JSON-schema constraints, prompt-level injection mitigation for untrusted PDF inputs, and deterministic regex fallbacks for PII extraction.
* **Highly Optimized Backend:** Profiled under 50 concurrent threads using `py-spy`. Diagnosed and resolved PostgreSQL connection-pool starvation to improve throughput by ~35% (21 → 28.5 RPS avg) while maintaining ~65ms single-request latency.

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **Backend:** FastAPI, Python, Uvicorn
* **Database & ORM:** PostgreSQL, SQLAlchemy, Alembic (Migrations)
* **AI & NLP:** Google Gemini 2.5 Flash, Sentence Transformers
* **Vector Store:** ChromaDB
* **DevOps & Profiling:** Docker, Docker Compose, py-spy

## 🚦 Getting Started

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* A [Google Gemini API Key](https://aistudio.google.com/).

### 1. Clone the Repository
```bash
git clone https://github.com/AIResumeLabs/ai-resume-platform.git
cd ai-resume-platform
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory and add your Gemini API key. The database URL is pre-configured for the Docker network.

```text
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://postgres:postgrespassword@db:5432/resume_matcher_db
```

### 3. Launch the Application

Build and start the entire stack (Frontend, Backend, and Database) using Docker Compose.

```bash
docker compose up --build
```

*(To run in the background, append `-d` to the command).*

### 4. Access the Platform

Once the containers are running, the platform is available at the following local endpoints:

* **Web UI (Streamlit):** http://localhost:8501
* **API Documentation (Swagger UI):** http://localhost:8000/docs
* **Database (External Access):** `localhost:5433` (Username: `postgres`, Password: `postgrespassword`)

## 🧠 Architecture Deep-Dive: The Two-Pass Pipeline

To ensure high fidelity in data extraction, the system routes resumes through two distinct AI processing phases:

1. **Pass 1 (Literal Extraction):** Scans the raw text with strict constraints to *only* extract explicit, literal skills and keywords. No inference or evaluation is allowed.
2. **Pass 2 (Semantic Inference & Scoring):** Feeds the literal list and original text back to the LLM to deduplicate terms, infer foundational skills based on context (e.g., inferring "Problem Solving" from high competitive programming ratings), and assign a 1-5 proficiency score backed by specific quoted achievements from the text.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome. Feel free to open an issue or submit a Pull Request.

## 📝 License

This project is licensed under the [MIT License](LICENSE).
