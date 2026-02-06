# backend/rag_service.py
from sentence_transformers import SentenceTransformer
import psycopg2
import numpy as np

# Load the model once
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text: str) -> list[float]:
    """Generate embedding for a given text."""
    if not text or not text.strip():
        raise ValueError("Text must not be empty")

    embedding = model.encode(
        text,
        normalize_embeddings=True
    )

    return embedding.tolist()


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """
    Split a long text into chunks of approximately chunk_size words.
    """
    words = text.split()
    chunks = [' '.join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]
    return chunks


def search_similar_sources(query: str, top_k: int = 5) -> list[dict]:
    """
    Search for the top-k most similar academic sources using pgvector.
    Returns a list of dictionaries with id, title, content, and distance.
    """
    query_embedding = embed_text(query)

    # Connect to PostgreSQL
    conn = psycopg2.connect(
    host="academic_postgres",
    port=5432,
    database="academic_helper",
    user="postgres",
    password="123456"
)

    cur = conn.cursor()

    # Perform similarity search using pgvector <-> operator
    sql = """
    SELECT id, title, content,
       embedding <-> %s::vector AS distance
    FROM academic_sources
    ORDER BY embedding <-> %s::vector
    LIMIT %s;
    """
    cur.execute(sql, (query_embedding, query_embedding, top_k))
    results = cur.fetchall()

    cur.close()
    conn.close()

    # Convert results to a friendly list of dicts
    return [
        {"id": r[0], "title": r[1], "content": r[2], "distance": float(r[3])}
        for r in results
    ]
