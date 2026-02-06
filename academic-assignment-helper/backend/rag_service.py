# backend/rag_service.py
from typing import List, Dict
from fastapi import HTTPException
from sentence_transformers import SentenceTransformer
import psycopg2
from openai import OpenAI
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from typing import Optional

# ----------------------------
# Load embedding model once
# ----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# Load OpenAI API key from environment
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
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
    query: Optional[str] = None
    top_k: int = 5

class Source(BaseModel):
    title: str
    content: str

class AssignmentAnalysisRequest(BaseModel):
    assignment_text: str
    top_k: int = 5
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
    context_text = "\n\n".join([f"{s.title}: {s.content}" for s in sources])

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
    input=prompt,
    model="openai/gpt-oss-20b",
)
        return response.output_text
        # return "".join([item["text"] for msg in response.output for item in msg["content"] if item["type"] == "output_text"]).strip()
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
    
def analyze_assignment(
    assignment_text: str,
    sources: List[Dict],
) -> Dict:
    """
    Perform AI-based academic analysis grounded on retrieved academic sources.
    """

    # 1. Prepare RAG context
    context_text = "\n\n".join(
        f"Title: {s['title']}\nContent: {s['content']}"
        for s in sources
    )

    # 2. Strict structured prompt
    prompt = f"""
You are an academic integrity assistant.

Analyze the student assignment using ONLY the academic sources provided.
Return **strict JSON ONLY** with no extra text.

Keys required:
- topic (string)
- key_themes (array of strings)
- suggested_sources (array of source titles)
- plagiarism_score (number between 0 and 1)
- flagged_sections (array of short text excerpts)
- research_suggestions (string)
- citation_recommendations (string)

Academic Sources:
{context_text}

Student Assignment:
{assignment_text}

JSON Response:
"""

    try:
        response = client.responses.create(
            model="openai/gpt-oss-20b",
            input=prompt,
        )

        # Extract text safely
        output_text = response.output_text.strip()

        # Defensive JSON parsing
        import json
        result = json.loads(output_text)

        return result

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="AI response was not valid JSON"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI analysis error: {e}"
        )
# ----------------------------
# Helper: Store analysis results
# ----------------------------
import json

def store_analysis_results(assignment_id: int, analysis: dict) -> int:
    """
    Stores the AI-generated assignment analysis into PostgreSQL.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        sql = """
        INSERT INTO analysis_results (
            assignment_id,
            suggested_sources,
            plagiarism_score,
            flagged_sections,
            research_suggestions,
            citation_recommendations,
            confidence_score,
            analyzed_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING id;
        """

        # Convert lists/dicts to JSON strings
        suggested_sources_json = json.dumps(analysis.get("suggested_sources", []))
        flagged_sections_json = json.dumps(analysis.get("flagged_sections", []))

        cur.execute(
            sql,
            (
                assignment_id,
                suggested_sources_json,
                analysis.get("plagiarism_score", 0.0),
                flagged_sections_json,
                analysis.get("research_suggestions", ""),
                analysis.get("citation_recommendations", ""),
                analysis.get("confidence_score", None)
            )
        )
        analysis_id = cur.fetchone()[0]
        conn.commit()
        return analysis_id
    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database insert error: {e}")
    finally:
        cur.close()
        conn.close()


@router.post("/analyze_assignment/{assignment_id}")
async def analyze_and_store(assignment_id: int, request: RAGRequest):
    # 1. Fetch assignment text
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT original_text FROM assignments WHERE id = %s;", (assignment_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        assignment_text = row[0]
        if not assignment_text:
            raise HTTPException(status_code=400, detail="Assignment has no extracted text")
    finally:
        cur.close()
        conn.close()

    # 2. Determine RAG query
    rag_query = request.query if request.query else assignment_text

    # 3. Search relevant sources
    sources_data = search_similar_sources(rag_query, request.top_k)
    if not sources_data:
        raise HTTPException(status_code=404, detail="No sources found")
    sources = [dict(title=r["title"], content=r["content"]) for r in sources_data]

    # 4. Run AI analysis
    analysis = analyze_assignment(assignment_text, sources)

    # 5. Store results in DB
    analysis_id = store_analysis_results(assignment_id, analysis)

    # 6. Return combined response
    return {
        "assignment_id": assignment_id,
        "analysis_id": analysis_id,
        "analysis": analysis,
        "sources_used": [s["title"] for s in sources]
    }



