from sqlalchemy import text
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.database import SessionLocal
from app.embeddings import generate_embedding
from app.vector_store import qdrant_client, COLLECTION_NAME
MIN_VECTOR_SCORE = 0.35

def keyword_search(tenant_id: str, query: str, top_k: int = 10):
    db = SessionLocal()
    try:
        sql = text("""
            SELECT id, content, ts_rank(to_tsvector('english', content), plainto_tsquery('english', :query)) AS rank
            FROM chunks
            WHERE tenant_id = :tenant_id
              AND to_tsvector('english', content) @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC
            LIMIT :top_k
        """)
        rows = db.execute(sql, {"tenant_id": tenant_id, "query": query, "top_k": top_k}).fetchall()
        return [(str(row.id), row.content) for row in rows]
    finally:
        db.close()
def vector_search(tenant_id: str, query: str, top_k: int = 10):
    vector = generate_embedding(query)
    results = qdrant_client.search(
collection_name=COLLECTION_NAME,
query_vector=vector,
query_filter=Filter(
    must=[FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))]
),
limit=top_k,
)
    results = [point for point in results if point.score >= MIN_VECTOR_SCORE]
    return [(str(point.id), point.payload.get("content", "")) for point in results]
def reciprocal_rank_fusion(keyword_results, vector_results, k=60):
    scores = {}
    content_map = {}
    for rank, (chunk_id, content) in enumerate(keyword_results, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)
        content_map[chunk_id] = content
    for rank, (chunk_id, content) in enumerate(vector_results, start=1):
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)
        content_map[chunk_id] = content
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(chunk_id, content_map[chunk_id], score) for chunk_id, score in ranked]


def hybrid_search(tenant_id: str, query: str, top_k: int = 5):
    keyword_results = keyword_search(tenant_id, query, top_k=10)
    vector_results = vector_search(tenant_id, query, top_k=10)
    fused = reciprocal_rank_fusion(keyword_results, vector_results)
    return fused[:top_k]