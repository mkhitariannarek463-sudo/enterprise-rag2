from sqlalchemy import text

from app.database import SessionLocal
from app.retrieval import hybrid_search, keyword_search, vector_search

QUERIES = [
    "What is the capital of Armenia?",
    "Yerevan",
    "What is chlorophyll?",
    "photosynthesis",
    "certificate of completion",
]


def main():
    db = SessionLocal()
    tenants = [str(r.id) for r in db.execute(text("SELECT id FROM tenants")).fetchall()]
    own = {}
    for t in tenants:
       rows = db.execute(text("SELECT id FROM chunks WHERE tenant_id = :t"), {"t": t}).fetchall()
       own[t] = {str(r.id) for r in rows}
    checks = 0
    leaks = 0
    for t in tenants:
        for query in QUERIES:
            for name, fn in (("keyword", keyword_search), ("vector", vector_search), ("hybrid", hybrid_search)):
                ids = [str(item[0]) for item in fn(t, query, 10)]
                checks += 1
                foreign = [i for i in ids if i not in own[t]]
                if foreign:
                    leaks += 1
                    print("LEAK:", name, "| tenant", t, "|", query, "|", len(foreign), "foreign chunks")
    db.close()
    print("Tenants: %d | checks: %d | leaks: %d" % (len(tenants), checks, leaks))


if __name__ == "__main__":
    main()