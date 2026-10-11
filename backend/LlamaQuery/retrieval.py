# similarity search for llamaQuery, kept free of aws and openai imports so it can be tested on its own

import math

DEFAULT_TOP_K = 5


def cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    return dot / (mag_a * mag_b + 1e-9)


def rank_chunks(query_embedding, chunks, top_k=DEFAULT_TOP_K):
    """return the top_k (similarity, text) pairs, most similar first

    chunks are dynamodb items, so embeddings arrive as decimals, and chunks
    without an embedding are skipped
    """
    scored = []
    for chunk in chunks:
        embedding = chunk.get("embedding")
        if embedding:
            emb_floats = [float(v) for v in embedding]
            sim = cosine_similarity(query_embedding, emb_floats)
            scored.append((sim, chunk["text"]))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]
