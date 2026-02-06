# PlagiarismDetector – Academic Assignment Helper (RAG System)

A **Retrieval-Augmented Generation (RAG)** powered system for analyzing student academic assignments.

Leverages AI to:

- Identify topics and key themes
- Suggest relevant academic sources
- Detect potential plagiarism
- Provide research ideas & citation recommendations

All analysis is **grounded in real academic sources** stored in PostgreSQL with vector embeddings (pgvector).

## Features

- Upload student assignments (`.txt` files supported)
- Automatic text extraction
- Semantic similarity search against academic corpus using **pgvector**
- Structured AI analysis (JSON output)
- Persistent storage of results and matched sources
- REST API to retrieve assignment analyses

## Architecture

1. **Ingestion Pipeline**  
   Academic papers/articles → chunking → embeddings → PostgreSQL (pgvector)

2. **Assignment Processing**  
   Student file → text → embedding → similarity search → top-k relevant sources

3. **AI Generation**  
   LLM receives assignment + retrieved context → produces structured analysis

4. **Storage & API**  
   Results saved in DB → accessible via FastAPI endpoints

## Tech Stack

| Component            | Technology                     |
|----------------------|--------------------------------|
| Backend API          | FastAPI                        |
| Database             | PostgreSQL + **pgvector**      |
| Embeddings / AI      | OpenAI / compatible LLM        |
| Containerization     | Docker & Docker Compose        |
| Workflow Automation  | **n8n**                        |
| Authentication       | JWT                            |

## Setup & Installation

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (optional – local development)

### Quick start (all-in-one)

1. Clone the repository

```bash
git clone https://github.com/abenezertileye/PlagiarismDetector.git
cd PlagiarismDetector/backend
```

2. Create `.env` file in the `backend/` folder

```env
# Example .env file content - change values!
DATABASE_URL=postgresql+psycopg://user:password@postgres:5432/academic_db
OPENAI_API_KEY=sk-...
JWT_SECRET_KEY=your-very-long-random-secret-here-please-change-this
```

3. Start everything with Docker Compose

```bash
docker-compose up --build
```

After build & startup finishes you should have:

- FastAPI backend running at: http://localhost:8000
- PostgreSQL + pgvector database
- Swagger UI / docs at: http://localhost:8000/docs

## Basic Usage

### Upload an assignment file

```http
POST http://localhost:8000/assignments/upload
Content-Type: multipart/form-data

file → (select your assignment.txt)
```

### Trigger analysis

```http
POST http://localhost:8000/rag/analyze_assignment/{assignment_id}

{
  "query": "Paste full assignment text here if you want to override uploaded file",
  "top_k": 4
}
```

Example response:

```json
{
  "assignment_id": 1,
  "analysis_id": 1,
  "analysis": {
    "topic": "Transformer Models in NLP",
    "key_themes": ["Self-Attention", "Pre-training", "Fine-tuning"],
    "suggested_sources": ["Attention Is All You Need", "BERT paper"],
    "plagiarism_score": 0.18,
    "flagged_sections": ["...exact matching paragraph..."],
    "research_suggestions": "Consider mentioning FlashAttention or Mixture-of-Experts variants...",
    "citation_recommendations": "Vaswani et al. (2017), Devlin et al. (2019)"
  },
  "sources_used": [
    "Attention Is All You Need (2017)",
    "BERT: Pre-training of Deep Bidirectional Transformers..."
  ]
}
```

## n8n Workflow (optional automation)

Run n8n in a separate terminal / container:

```bash
docker run -it --rm -p 5678:5678 -v "${HOME}/.n8n:/home/node/.n8n" n8nio/n8n
```

Then open http://localhost:5678  
→ import the workflow JSON file from the repository  
→ activate the workflow

## Database Tables (main ones)

- `students`  
  id, email, password_hash, full_name, student_id

- `assignments`  
  id, student_id, filename, original_text, uploaded_at

- `academic_sources`  
  id, title, content, embedding (vector)

- `analysis_results`  
  id, assignment_id, suggested_sources (jsonb), plagiarism_score, flagged_sections (jsonb), research_suggestions, citation_recommendations, confidence_score, analyzed_at

## Security

- JWT authentication
- Passwords hashed
