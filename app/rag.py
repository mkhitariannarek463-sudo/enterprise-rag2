from app.retrieval import hybrid_search
from app.llm import generate_answer


def ask(tenant_id: str, query: str, top_k: int = 5) -> str:
    results = hybrid_search(tenant_id, query, top_k=top_k)
    context_chunks = [content for _, content, _ in results]
    if not context_chunks:
        return "No relevant information found in the documents."
    return generate_answer(query, context_chunks)