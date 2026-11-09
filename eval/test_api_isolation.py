import secrets
import uuid

import fitz
import requests

BASE = "http://127.0.0.1:8000"


def register_and_login(label):
    suffix = uuid.uuid4().hex[:8]
    email = "iso_%s_%s@isolation.test" % (label, suffix)
    password = secrets.token_urlsafe(12)
    r = requests.post(
        BASE + "/auth/register",
        json={"email": email, "password": password, "tenant_name": "Iso-%s-%s" % (label, suffix)},
        timeout=30,
    )
    r.raise_for_status()
    r = requests.post(BASE + "/auth/login", data={"username": email, "password": password}, timeout=30)
    r.raise_for_status()
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def make_pdf(code):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Confidential. The secret project codename of company A is %s." % code)
    data = doc.tobytes()
    doc.close()
    return data


def ask(headers, question):
    r = requests.post(BASE + "/ask", json={"query": question}, headers=headers, timeout=120)
    return r.text


def main():
    code = "ZEPHYR" + uuid.uuid4().hex[:6].upper()
    headers_a = register_and_login("a")
    headers_b = register_and_login("b")
    r = requests.post(
        BASE + "/documents/upload",
        files={"file": ("secret_a.pdf", make_pdf(code), "application/pdf")},
        headers=headers_a,
        timeout=120,
        )
    print("Upload by A:", r.status_code)
    question = "What is the secret project codename of company A?"
    text_a = ask(headers_a, question)
    text_b = ask(headers_b, question)
    a_sees = code in text_a
    b_sees = code in text_b
    no_token = requests.post(BASE + "/ask", json={"query": question}, timeout=30).status_code
    bad_token = requests.post(
        BASE + "/ask", json={"query": question}, headers={"Authorization": "Bearer invalid"}, timeout=30
    ).status_code
    print("A sees own secret:", a_sees, "(must be True)")
    print("B sees A secret:", b_sees, "(must be False)")
    print("No token status:", no_token, "(must be 401 or 403)")
    print("Bad token status:", bad_token, "(must be 401 or 403)")
    ok = a_sees and not b_sees and no_token in (401, 403) and bad_token in (401, 403)
    print("RESULT:", "PASS" if ok else "FAIL")
if __name__ == "__main__":
    main()