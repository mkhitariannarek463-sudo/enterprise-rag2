from sentence_transformers import CrossEncoder

MODEL_NAME = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
_model = None


def get_model():
    global _model
    if _model is None:
        _model = CrossEncoder(MODEL_NAME)
    return _model


def rerank(query, results, top_k=5):
    if not results:
        return []
    pairs = [(query, content) for _, content, _ in results]
    scores = get_model().predict(pairs)
    ranked = sorted(zip(results, scores), key=lambda item: item[1], reverse=True)
    return [(chunk_id, content, float(score)) for (chunk_id, content, _), score in ranked[:top_k]]