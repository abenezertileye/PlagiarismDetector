from fastapi import APIRouter
from rag_service import search_similar_sources

router = APIRouter()

@router.get("/")
def get_sources(query: str, top_k: int = 5):
    results = search_similar_sources(query, top_k=top_k)
    return {"results": results}
