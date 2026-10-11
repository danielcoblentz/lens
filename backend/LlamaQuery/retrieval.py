"""Similarity search for LlamaQuery.

Kept free of AWS and OpenAI imports so it can be imported and tested on its own.
"""

import math

DEFAULT_TOP_K = 5


def cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    return dot / (mag_a * mag_b + 1e-9)


def rank_chunks(query_embedding, chunks, top_k=DEFAULT_TOP_K):
    """score every chunk against the query embedding and return the best ones.

    chunks are DynamoDB items, so embeddings come back as Decimal and need
    converting to float first. chunks with no embedding are skipped.
    returns a list of (similarity, text) sorted from most to least similar.
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
