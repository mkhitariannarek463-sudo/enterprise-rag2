from anthropic import Anthropic
from app.config import get_settings

settings = get_settings()
client = Anthropic(api_key=settings.anthropic_api_key)


def generate_answer(query: str, context_chunks: list) -> str:
    context_text = "\n\n".join(context_chunks)
    prompt = f"""You are a helpful assistant. Answer the question using ONLY the context below. If the answer is not in the context, say you don't know.

Context:
{context_text}

Question: {query}

Answer:"""

    message = client.messages.create(
        model=settings.llm_model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in message.content if block.type == 'text')