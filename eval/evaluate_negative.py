from pathlib import Path

from app.rag import NO_INFO_ANSWER, ask
from app.retrieval import hybrid_search
from eval.evaluate import get_tenant_id


def main():
    lines = Path("eval/negative_questions.txt").read_text(encoding="utf-8").splitlines()
    questions = [line.strip() for line in lines if line.strip()]
    tenant_id = get_tenant_id()
    retrieval_rejected = 0
    answer_rejected = 0
    for question in questions:
        chunks = hybrid_search(tenant_id, question, 5)
        if not chunks:
            retrieval_rejected += 1
        result = ask(tenant_id, question)
        rejected = result["answer"] == NO_INFO_ANSWER
        if rejected:
            answer_rejected += 1
        print("REJECTED" if rejected else "ANSWERED", "| chunks:", len(chunks), "|", question)
        if not rejected:
            print("   ->", result["answer"])
    total = len(questions)
    print("Retrieval rejection: %d/%d" % (retrieval_rejected, total))
    print("Final rejection rate: %d/%d = %.0f%%" % (answer_rejected, total, 100 * answer_rejected / total))


if __name__ == "__main__":
    main()