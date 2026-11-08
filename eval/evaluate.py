import json
from pathlib import Path

from sqlalchemy import text

from app.database import SessionLocal
from app.retrieval import hybrid_search, keyword_search, vector_search

TOP_K = 5
EMAIL = "test@example.com"


def get_tenant_id() -> str:
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT tenant_id FROM users WHERE email = :email"),
            {"email": EMAIL},
        ).fetchone()
        return str(row.tenant_id)
    finally:
        db.close()
def first_hit_rank(results, must_contain):
    for rank, item in enumerate(results, start=1):
        content = item[1]
        if must_contain.lower() in content.lower():
            return rank
    return None


def evaluate(name, search_fn, tenant_id, questions):
    hits = 0
    reciprocal_sum = 0.0
    misses = []
    for q in questions:
        results = search_fn(tenant_id, q["question"], TOP_K)
        rank = first_hit_rank(results, q["must_contain"])
        if rank is None:
            misses.append(q["question"])
        else:
            hits += 1
            reciprocal_sum += 1 / rank
    total = len(questions)
    print(f"\n=== {name} ===")
    print(f"Hit rate@{TOP_K}: {hits}/{total} = {hits / total:.0%}")
    print(f"MRR: {reciprocal_sum / total:.3f}")
    for m in misses:
        print(f"  MISS: {m}")
def main():
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    tenant_id = get_tenant_id()
    evaluate("keyword only", keyword_search, tenant_id, questions)
    evaluate("vector only", vector_search, tenant_id, questions)
    evaluate("hybrid (RRF)", hybrid_search, tenant_id, questions)


if __name__ == "__main__":
    main()