# backend/rag_service.py
from sentence_transformers import SentenceTransformer
import psycopg2
from openai import OpenAI
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

# ----------------------------
# Load embedding model once
# ----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load OpenAI API key from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment!")

# ----------------------------
# FastAPI router
# ----------------------------
router = APIRouter()

# ----------------------------
# Pydantic models
# ----------------------------
class RAGRequest(BaseModel):
    query: str
    top_k: int = 5

class Source(BaseModel):
    title: str
    content: str

# ----------------------------
# Helper: DB connection
# ----------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "academic_postgres"),
            port=os.getenv("POSTGRES_PORT", 5432),
            database=os.getenv("POSTGRES_DB", "academic_helper"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "123456")
        )
        return conn
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")

# ----------------------------
# Helper: Embed text
# ----------------------------
def embed_text(text: str) -> list[float]:
    if not text.strip():
        raise ValueError("Text must not be empty")
    return model.encode(text, normalize_embeddings=True).tolist()

# ----------------------------
# Helper: Search similar sources
# ----------------------------
def search_similar_sources(query: str, top_k: int = 5) -> List[dict]:
    query_embedding = embed_text(query)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        sql = """
        SELECT id, title, content AS content,
               embedding <-> %s::vector AS distance
        FROM academic_sources
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
        """
        cur.execute(sql, (query_embedding, query_embedding, top_k))
        results = cur.fetchall()
        return [
            {"id": r[0], "title": r[1], "content": r[2], "distance": float(r[3])}
            for r in results
        ]
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {e}")
    finally:
        cur.close()
        conn.close()


# ----------------------------
# Helper: Chunk large text
# ----------------------------
def chunk_text(text: str, max_words: int = 500) -> List[str]:
    words = text.split()
    return [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

# ----------------------------
# Helper: Generate grounded answer
# ----------------------------
def generate_answer(query: str, sources: list[dict]) -> str:
    # Combine sources
    context_text = "\n\n".join([f"{s['title']}: {s['content']}" for s in sources])

    prompt = f"""
You are an academic assistant. Answer the question below using ONLY the sources provided.
Do not include any information not present in the sources.

Sources:
{context_text}

Question: {query}

Answer:
"""

    try:
        response = client.responses.create(
            model="gpt-4o",  # or "gpt-3.5-turbo" if your key allows
            input=prompt,
            temperature=0,
            max_output_tokens=300
        )
        # Extract text from output array
        return "".join([item["text"] for msg in response.output for item in msg["content"] if item["type"] == "output_text"]).strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")


# ----------------------------
# FastAPI endpoint
# ----------------------------
@router.post("/answer")
async def rag_answer(request: RAGRequest):
    results = search_similar_sources(request.query, request.top_k)
    if not results:
        raise HTTPException(status_code=404, detail="No sources found")

    sources = [Source(title=r["title"], content=r["content"]) for r in results]
    answer = generate_answer(request.query, sources)

    return {
        "query": request.query,
        "answer": answer,
        "sources": [s.title for s in sources]
    }
