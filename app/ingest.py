from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Document, Chunk
from app.document_processor import extract_text_from_pdf, chunk_text
from app.embeddings import generate_embedding
from app.vector_store import ensure_collection, upsert_chunk
from app.exceptions import EmptyDocumentError


def ingest_document(file_path: str, tenant_id: str, filename: str):
    ensure_collection()
    db: Session = SessionLocal()
    try:
        text = extract_text_from_pdf(file_path)
        chunks = chunk_text(text)
        if not chunks:
             raise EmptyDocumentError("No text could be extracted from this PDF")
                    
        document = Document(tenant_id=tenant_id, filename=filename)
        db.add(document)
        db.commit()
        db.refresh(document)


        for index, chunk_content in enumerate(chunks):
            chunk = Chunk(
                document_id=document.id,
                tenant_id=tenant_id,
                content=chunk_content,
                chunk_index=index,)
            db.add(chunk)
            db.commit()
            db.refresh(chunk)

            vector = generate_embedding(chunk_content)
            upsert_chunk(
                str(chunk.id),
                vector,
                {
                    "document_id": str(document.id),
                    "tenant_id": str(tenant_id),
                    "chunk_index": index,
                    "content": chunk_content,
                },
            )

        return document.id
    finally:
        db.close()