"""Text chunking for LlamaParse.

Kept free of AWS and OpenAI imports so it can be imported and tested on its own.
"""


def recursive_chunk_text(text, chunk_size=800, chunk_overlap=100, separators=None):
    """split text by trying separators in order: paragraphs, lines, sentences, words.
    overlap between chunks keeps context at the boundaries."""
    if separators is None:
        separators = ["\n\n", "\n", ". ", " "]

    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    # pick the first separator that actually appears in the text
    chosen_separator = separators[-1]
    for sep in separators:
        if sep in text:
            chosen_separator = sep
            break

    parts = text.split(chosen_separator)
    chunks = []
    current_chunk = ""

    for part in parts:
        part_with_sep = part + chosen_separator if chosen_separator != " " else part + " "

        if len(current_chunk) + len(part_with_sep) <= chunk_size:
            current_chunk += part_with_sep
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            if len(part_with_sep) > chunk_size:
                # chunk is still too big, try the next separator down
                remaining_separators = separators[separators.index(chosen_separator) + 1:]
                if remaining_separators:
                    sub_chunks = recursive_chunk_text(part, chunk_size, chunk_overlap, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    # no separators left, just hard split
                    for i in range(0, len(part), chunk_size - chunk_overlap):
                        chunks.append(part[i:i + chunk_size].strip())
                    current_chunk = ""
            else:
                # add overlap from the previous chunk to maintain context
                if chunks and chunk_overlap > 0:
                    overlap_text = chunks[-1][-chunk_overlap:]
                    current_chunk = overlap_text + " " + part_with_sep
                else:
                    current_chunk = part_with_sep

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
