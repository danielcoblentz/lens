from chunking import recursive_chunk_text


def build_paragraphs(count, body="clause text " * 8):
    return "\n\n".join("Section {}. {}".format(i, body) for i in range(count))


class TestShortDocuments:
    def test_document_shorter_than_chunk_size_yields_one_chunk(self):
        assert recursive_chunk_text("A short contract.", chunk_size=800) == [
            "A short contract."
        ]

    def test_document_exactly_chunk_size_yields_one_chunk(self):
        assert len(recursive_chunk_text("a" * 800, chunk_size=800)) == 1

    def test_empty_and_whitespace_only_documents_yield_no_chunks(self):
        assert recursive_chunk_text("", chunk_size=800) == []
        assert recursive_chunk_text("   \n\n  ", chunk_size=800) == []

    def test_short_document_is_stripped(self):
        assert recursive_chunk_text("  padded contract  ", chunk_size=800) == [
            "padded contract"
        ]


class TestChunkSize:
    def test_no_chunk_exceeds_chunk_size(self):
        chunks = recursive_chunk_text(build_paragraphs(20), chunk_size=200, chunk_overlap=0)
        assert len(chunks) > 1
        assert all(len(c) <= 200 for c in chunks)

    def test_long_document_splits_into_multiple_chunks(self):
        doc = build_paragraphs(6)
        assert len(doc) > 200
        assert len(recursive_chunk_text(doc, chunk_size=200, chunk_overlap=0)) == 6

    def test_text_with_no_separators_is_hard_split_by_size(self):
        # 500 chars, stride of chunk_size - chunk_overlap = 80
        chunks = recursive_chunk_text("X" * 500, chunk_size=100, chunk_overlap=20)
        assert [len(c) for c in chunks] == [100, 100, 100, 100, 100, 100, 20]

    def test_every_chunk_is_non_empty(self):
        chunks = recursive_chunk_text(build_paragraphs(10), chunk_size=150, chunk_overlap=30)
        assert chunks
        assert all(c.strip() for c in chunks)


class TestOverlap:
    def test_each_chunk_begins_with_the_tail_of_the_previous_chunk(self):
        overlap = 40
        chunks = recursive_chunk_text(build_paragraphs(6), chunk_size=200, chunk_overlap=overlap)
        assert len(chunks) > 1
        for previous, current in zip(chunks, chunks[1:]):
            assert current.startswith(previous[-overlap:])

    def test_zero_overlap_produces_no_repeated_text(self):
        chunks = recursive_chunk_text(build_paragraphs(6), chunk_size=200, chunk_overlap=0)
        assert len(chunks) > 1
        for previous, current in zip(chunks, chunks[1:]):
            assert not current.startswith(previous[-40:])

    def test_overlap_makes_chunks_longer_than_no_overlap(self):
        doc = build_paragraphs(6)
        without = recursive_chunk_text(doc, chunk_size=200, chunk_overlap=0)
        with_overlap = recursive_chunk_text(doc, chunk_size=200, chunk_overlap=40)
        assert sum(len(c) for c in with_overlap) > sum(len(c) for c in without)


class TestSeparators:
    def test_paragraph_breaks_are_preferred_over_mid_paragraph_splits(self):
        chunks = recursive_chunk_text(build_paragraphs(6), chunk_size=200, chunk_overlap=0)
        # every chunk starts at a paragraph boundary, so none is split mid-section
        assert all(c.startswith("Section ") for c in chunks)

    def test_falls_back_to_line_breaks_when_there_are_no_paragraph_breaks(self):
        doc = "\n".join("Line {} {}".format(i, "w" * 30) for i in range(10))
        chunks = recursive_chunk_text(doc, chunk_size=120, chunk_overlap=0)
        assert all(c.startswith("Line ") for c in chunks)
        assert "\n" in chunks[0]

    def test_falls_back_to_sentence_breaks_when_there_are_no_newlines(self):
        doc = ". ".join("Sentence number {} is here".format(i) for i in range(20)) + "."
        chunks = recursive_chunk_text(doc, chunk_size=150, chunk_overlap=0)
        assert len(chunks) > 1
        assert all(c.startswith("Sentence number ") for c in chunks)

    def test_custom_separator_list_is_respected(self):
        doc = "|".join("field {}".format(i) * 10 for i in range(6))
        chunks = recursive_chunk_text(doc, chunk_size=200, chunk_overlap=0, separators=["|"])
        assert len(chunks) > 1
        assert all(c.startswith("field ") for c in chunks)

    def test_no_content_is_lost_when_splitting_on_paragraphs(self):
        doc = build_paragraphs(6)
        chunks = recursive_chunk_text(doc, chunk_size=200, chunk_overlap=0)
        rejoined = "".join(chunks).replace(" ", "")
        assert rejoined == doc.replace(" ", "").replace("\n", "")
