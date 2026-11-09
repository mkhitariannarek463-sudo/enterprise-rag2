import json
from pathlib import Path

from app.rag import NO_INFO_ANSWER, ask
from eval.evaluate import get_tenant_id


def main():
    questions = json.loads(Path("eval/questions.json").read_text(encoding="utf-8"))
    tenant_id = get_tenant_id()
    total = len(questions)
    answered = 0
    correct = 0
    cited_ok = 0
    for q in questions:
        result = ask(tenant_id, q["question"])
        gold = q["must_contain"].lower()
        if result["answer"] == NO_INFO_ANSWER:
            print("NO ANSWER |", q["question"])
            continue
        answered += 1
        is_correct = gold in result["answer"].lower()
        is_cited = any(gold in s["text"].lower() for s in result["sources"])
        if is_correct:
            correct += 1
        if is_cited:
            cited_ok += 1
        if not (is_correct and is_cited):
            print("CHECK | correct:", is_correct, "| cited:", is_cited, "|", q["question"])
            print("   ->", result["answer"])
    print("Answered: %d/%d" % (answered, total))
    print("Answer contains gold value: %d/%d" % (correct, total))
    print("Cited source contains gold value: %d/%d" % (cited_ok, total))


if __name__ == "__main__":
    main()