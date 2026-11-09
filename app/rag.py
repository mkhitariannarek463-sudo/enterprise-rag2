import json

from app.llm import get_llm_provider
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.retrieval import hybrid_search
from app.reranker import rerank

NO_INFO_ANSWER = "No relevant information found in the documents."


def parse_llm_reply(reply: str) -> dict:
    start = reply.find("{")
    end = reply.rfind("}")
    if start == -1 or end == -1:
        return {"answer": reply.strip(), "sources": []}
    try:
        data = json.loads(reply[start : end + 1])
    except json.JSONDecodeError:
        return {"answer": reply.strip(), "sources": []}
    return {
        "answer": str(data.get("answer", "")),
        "sources": [n for n in data.get("sources", []) if isinstance(n, int)],
    }


def ask(tenant_id: str, query: str, top_k: int = 5) -> dict:
    candidates = hybrid_search(tenant_id, query, top_k=10)
    results = rerank(query, candidates, top_k) if candidates else []
    chunks = [content for _, content, _ in results]
    if not chunks:
        return {"answer": NO_INFO_ANSWER, "sources": []}
    reply = get_llm_provider().generate(
        SYSTEM_PROMPT, build_user_prompt(query, chunks)
    )
    parsed = parse_llm_reply(reply)
    sources = [
        {"id": n, "text": chunks[n - 1]}
        for n in parsed["sources"]
        if 1 <= n <= len(chunks)
    ]
    if not sources: 
         return {"answer": NO_INFO_ANSWER, "sources": []}
    return {"answer": parsed["answer"], "sources": sources}