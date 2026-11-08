import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

st.set_page_config(page_title="Enterprise RAG")
st.title("Enterprise RAG")

if "token" not in st.session_state:
    st.session_state.token = None

with st.sidebar:
    st.header("Account")
    if st.session_state.token:
        st.success("Logged in")
        if st.button("Log out"):
            st.session_state.token = None
            st.rerun()
    else:
        tab_login, tab_register = st.tabs(["Log in", "Register"])
        with tab_login:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Log in"):
                response = requests.post(
                    f"{API_URL}/auth/login",
                    data={"username": email, "password": password},
                )
                if response.status_code == 200:
                    st.session_state.token = response.json()["access_token"]
                    st.rerun()
                else:
                    st.error("Wrong email or password")
        with tab_register:
            new_email = st.text_input("Email", key="register_email")
            new_password = st.text_input("Password (8+ characters)", type="password", key="register_password")
            organization = st.text_input("Organization name", key="register_org")
            if st.button("Create account"):
                response = requests.post(
                    f"{API_URL}/auth/register",
                    json={"email": new_email, "password": new_password, "tenant_name": organization},
                )
                if response.status_code == 201:
                    st.success("Account created. Now log in.")
                else:
                    st.error(f"Registration failed ({response.status_code})")
if not st.session_state.token:
 st.info("Please log in or register in the sidebar.")
 st.stop()

st.subheader("1. Upload a PDF")
uploaded = st.file_uploader("Choose a PDF file", type="pdf")
if uploaded is not None and st.button("Upload document"):
    with st.spinner("Indexing document..."):
        response = requests.post(
            f"{API_URL}/documents/upload",
            headers=auth_headers(),
            files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
            timeout=600,
        )
    if response.status_code == 200:
        st.success("Document indexed")
    else:
        st.error(f"Upload failed ({response.status_code}): {response.text}")

st.subheader("2. Ask a question")
question = st.text_input("Your question")
if st.button("Ask") and question:
    with st.spinner("Thinking..."):
        response = requests.post(
            f"{API_URL}/ask",
            headers=auth_headers(),
            json={"query": question},
            timeout=120,
        )
    if response.status_code == 200:
        st.write(response.json()["answer"])
    elif response.status_code == 401:
        st.session_state.token = None
        st.error("Session expired. Please log in again.")
    else:
        st.error(f"Error ({response.status_code})")