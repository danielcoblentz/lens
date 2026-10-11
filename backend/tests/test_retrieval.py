from decimal import Decimal

import pytest

from retrieval import cosine_similarity, rank_chunks


def chunk(text, embedding):
    return {"sessionId": "s1", "chunkId": text, "text": text, "embedding": embedding}


class TestCosineSimilarity:
    def test_identical_vectors_score_one(self):
        vec = [0.5, 0.25, 0.75, 1.0]
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors_score_zero(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
        assert cosine_similarity([1.0, 0.0, 0.0], [0.0, 0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors_score_minus_one(self):
        assert cosine_similarity([1.0, 2.0], [-1.0, -2.0]) == pytest.approx(-1.0)

    def test_similarity_ignores_magnitude(self):
        assert cosine_similarity([1.0, 1.0], [10.0, 10.0]) == pytest.approx(1.0)

    def test_known_value(self):
        # angle of 45 degrees between the two vectors
        assert cosine_similarity([1.0, 0.0], [1.0, 1.0]) == pytest.approx(0.7071067, abs=1e-6)

    def test_closer_vector_scores_higher(self):
        query = [1.0, 0.0]
        near = cosine_similarity(query, [0.9, 0.1])
        far = cosine_similarity(query, [0.1, 0.9])
        assert near > far

    def test_zero_vector_does_not_raise(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == pytest.approx(0.0)


class TestRankChunks:
    def test_nearest_vector_ranks_first(self):
        query = [1.0, 0.0, 0.0]
        chunks = [
            chunk("orthogonal", [0.0, 1.0, 0.0]),
            chunk("nearest", [0.99, 0.01, 0.0]),
            chunk("opposite", [-1.0, 0.0, 0.0]),
        ]
        ranked = rank_chunks(query, chunks)
        assert ranked[0][1] == "nearest"

    def test_results_are_sorted_by_descending_similarity(self):
        query = [1.0, 0.0]
        chunks = [
            chunk("far", [0.1, 0.9]),
            chunk("exact", [1.0, 0.0]),
            chunk("mid", [0.7, 0.7]),
        ]
        ranked = rank_chunks(query, chunks)
        assert [text for _, text in ranked] == ["exact", "mid", "far"]
        scores = [score for score, _ in ranked]
        assert scores == sorted(scores, reverse=True)

    def test_exact_match_scores_one(self):
        query = [0.3, 0.6, 0.1]
        ranked = rank_chunks(query, [chunk("exact", list(query))])
        assert ranked[0][0] == pytest.approx(1.0)

    def test_top_k_limits_the_number_of_results(self):
        query = [1.0, 0.0]
        chunks = [chunk("c{}".format(i), [1.0 - i / 10.0, i / 10.0]) for i in range(10)]
        assert len(rank_chunks(query, chunks, top_k=3)) == 3
        assert len(rank_chunks(query, chunks, top_k=1)) == 1

    def test_default_top_k_is_five(self):
        query = [1.0, 0.0]
        chunks = [chunk("c{}".format(i), [1.0 - i / 10.0, i / 10.0]) for i in range(10)]
        assert len(rank_chunks(query, chunks)) == 5

    def test_top_k_larger_than_chunk_count_returns_every_chunk(self):
        query = [1.0, 0.0]
        chunks = [chunk("a", [1.0, 0.0]), chunk("b", [0.0, 1.0])]
        assert len(rank_chunks(query, chunks, top_k=50)) == 2

    def test_dynamodb_decimal_embeddings_are_handled(self):
        query = [1.0, 0.0, 0.0]
        chunks = [
            chunk("decimal-far", [Decimal("0.0"), Decimal("1.0"), Decimal("0.0")]),
            chunk("decimal-near", [Decimal("1.0"), Decimal("0.0"), Decimal("0.0")]),
        ]
        ranked = rank_chunks(query, chunks)
        assert ranked[0][1] == "decimal-near"
        assert ranked[0][0] == pytest.approx(1.0)

    def test_chunks_without_embeddings_are_skipped(self):
        query = [1.0, 0.0]
        chunks = [
            {"text": "no embedding key"},
            {"text": "empty embedding", "embedding": []},
            chunk("has embedding", [1.0, 0.0]),
        ]
        ranked = rank_chunks(query, chunks)
        assert [text for _, text in ranked] == ["has embedding"]

    def test_no_chunks_returns_empty_list(self):
        assert rank_chunks([1.0, 0.0], []) == []
