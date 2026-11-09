import json
from pathlib import Path

from sqlalchemy import text

from app.database import SessionLocal
from app.retrieval import hybrid_search, keyword_search, vector_search
from app.reranker import rerank
from eval.evaluate import get_tenant_id

K_VALUES = [1, 3, 5]


def relevant_ids(db, tenant_id, doc, must_contain):
    sql = text("SELECT c.id FROM chunks c JOIN documents d ON c.document_id = d.id WHERE c.tenant_id = :t AND d.filename = :f AND c.content ILIKE :p")
    rows = db.execute(sql, {"t": tenant_id, "f": doc, "p": "%" + must_contain + "%"}).fetchall()
    return {str(r.id) for r in rows}


def evaluate(name, search_fn, tenant_id, questions, db):
    recall = {k: 0.0 for k in K_VALUES}
    precision = {k: 0.0 for k in K_VALUES}
    hit = {k: 0.0 for k in K_VALUES}
    mrr = 0.0
    counted = 0
    for q in questions:
        relevant = relevant_ids(db, tenant_id, q["doc"], q["must_contain"])
        if not relevant:
            print("NO GOLD CHUNK:", q["question"])
            continue
        results = search_fn(tenant_id, q["question"], max(K_VALUES))
        ids = [str(item[0]) for item in results]
        counted += 1
        for k in K_VALUES:
            found = len(set(ids[:k]) & relevant)
            recall[k] += found / len(relevant)
            precision[k] += found / k
            if found > 0:
                hit[k] += 1
        for rank, chunk_id in enumerate(ids, start=1):
            if chunk_id in relevant:
                mrr += 1 / rank
                break
    print(name)
    for k in K_VALUES:
        print("  K=%d | Recall %.2f | Precision %.2f | Hit %.2f" % (k, recall[k] / counted, precision[k] / counted, hit[k] / counted))
    print("  MRR %.3f" % (mrr / counted))

def hybrid_rerank(tenant_id, query, top_k=5):
    candidates = hybrid_search(tenant_id, query, 10)
    return rerank(query, candidates, top_k)

def main():
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    tenant_id = get_tenant_id()
    db = SessionLocal()
    evaluate("KEYWORD", keyword_search, tenant_id, questions, db)
    evaluate("VECTOR", vector_search, tenant_id, questions, db)
    evaluate("HYBRID", hybrid_search, tenant_id, questions, db)
    evaluate("HYBRID+RERANK", hybrid_rerank, tenant_id, questions, db)
    db.close()


if __name__ == "__main__":
    main()