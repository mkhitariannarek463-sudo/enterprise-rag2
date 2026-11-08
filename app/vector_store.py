from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import get_settings

settings = get_settings()

qdrant_client = QdrantClient(url=settings.qdrant_url)

COLLECTION_NAME = "documents"

def ensure_collection():
    collections = qdrant_client.get_collections().collections
    names = [c.name for c in collections]
    if COLLECTION_NAME not in names:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

def upsert_chunk(chunk_id: str, vector: list, payload: dict):
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[PointStruct(id=chunk_id, vector=vector, payload=payload)],
    )