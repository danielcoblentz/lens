"""
compare naive chunking with no overlap against the recursive chunker LlamaParse uses,
on the sample contract. retrieval is simulated with tf-idf, so no api key is needed.

usage: python scripts/compare_chunking.py [path/to/contract.pdf]
"""

import math
import os
import sys
from statistics import mean, stdev

from pypdf import PdfReader

REPO_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.join(REPO_ROOT, "backend", "LlamaParse"))
from chunking import recursive_chunk_text  # noqa: E402

DEFAULT_PDF = os.path.join(REPO_ROOT, "samples", "sample_legal_contract.pdf")
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def paragraph_chunk(text, max_chars=CHUNK_SIZE):
    """pack whole paragraphs up to max_chars, or cut fixed-size slices when the
    text has too few paragraph breaks, which is what pdf text usually looks like"""
    paragraphs = text.split("\n\n")

    if len(paragraphs) > 3:
        chunks, current = [], ""
        for para in paragraphs:
            if len(current) + len(para) < max_chars:
                current += para + "\n\n"
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = para + "\n\n"
        if current.strip():
            chunks.append(current.strip())
        return chunks
    else:
        return [text[i:i+max_chars].strip() for i in range(0, len(text), max_chars) if text[i:i+max_chars].strip()]


# -- test queries for the sample contract --

CLAUSE_QUERIES = [
    {"q": "What are the termination conditions?", "kw": ["terminat", "cancel", "end", "sole"]},
    {"q": "What referral fees are paid?", "kw": ["fee", "pay", "referral", "commission"]},
    {"q": "What is the confidentiality obligation?", "kw": ["confidential", "information", "parties"]},
    {"q": "What damages limitations exist?", "kw": ["damages", "limit", "liable"]},
    {"q": "What is the governing law?", "kw": ["govern", "law", "state"]},
    {"q": "What are affiliate responsibilities?", "kw": ["responsib", "affiliate", "shall"]},
    {"q": "What constitutes a breach?", "kw": ["breach", "warranty", "representation"]},
    {"q": "What notice is required?", "kw": ["notice", "written", "email"]},
    {"q": "What trademark restrictions apply?", "kw": ["trademark", "logo", "chase"]},
    {"q": "What is the agreement term?", "kw": ["term", "agreement", "period"]},
    {"q": "What indemnification applies?", "kw": ["indemnif", "defend", "harmless"]},
    {"q": "What warranty disclaimers exist?", "kw": ["warrant", "disclaim", "implied"]},
    {"q": "What is an approved account?", "kw": ["approved", "account", "credit"]},
    {"q": "How does link tracking work?", "kw": ["link", "track", "click"]},
    {"q": "How can the agreement be modified?", "kw": ["modif", "chang", "agree"]},
    {"q": "What logo licenses are granted?", "kw": ["licens", "logo", "grant"]},
    {"q": "What content is restricted?", "kw": ["restrict", "content", "unlawful"]},
    {"q": "What fee amount per approved account?", "kw": ["fee", "approved", "account", "paid"]},
    {"q": "Can Chase terminate without cause?", "kw": ["terminat", "without", "reason", "sole"]},
    {"q": "How is confidential info protected after termination?", "kw": ["confidential", "terminat", "information"]},
    {"q": "Who owns tracking data?", "kw": ["track", "data", "affiliate"]},
    {"q": "What logo usage rules apply?", "kw": ["logo", "use", "chase"]},
    {"q": "How are credit card accounts approved?", "kw": ["credit", "card", "account", "approved"]},
    {"q": "What customer data protections exist?", "kw": ["customer", "information", "data"]},
    {"q": "What site content rules apply?", "kw": ["site", "content", "affiliate"]},
    {"q": "What commercial use restrictions exist?", "kw": ["commercial", "use", "affiliate"]},
    {"q": "How does order processing work?", "kw": ["order", "process", "credit"]},
    {"q": "What is the service interruption policy?", "kw": ["service", "interrupt", "responsible"]},
    {"q": "What product description rules apply?", "kw": ["product", "description", "affiliate"]},
    {"q": "What enrollment requirements exist?", "kw": ["enroll", "registration", "program"]},
    {"q": "How are affiliate sales tracked?", "kw": ["track", "sales", "affiliate"]},
    {"q": "What independent investigation is needed?", "kw": ["independent", "investigat", "affiliate"]},
]


# -- retrieval simulation using tf-idf --

def compute_tfidf(documents):
    vocab, doc_freq = {}, {}
    tokenized = []

    for doc in documents:
        words = [''.join(c for c in w if c.isalnum()) for w in doc.lower().split()]
        words = [w for w in words if len(w) > 2]
        tokenized.append(words)
        for w in set(words):
            doc_freq[w] = doc_freq.get(w, 0) + 1
            if w not in vocab:
                vocab[w] = len(vocab)

    vectors = []
    n = len(documents)
    for words in tokenized:
        vec = [0.0] * len(vocab)
        if not words:
            vectors.append(vec)
            continue
        tf = {}
        for w in words:
            tf[w] = tf.get(w, 0) + 1
        for w, count in tf.items():
            if w in vocab:
                vec[vocab[w]] = (count / len(words)) * math.log(n / (doc_freq.get(w, 1) + 1))
        vectors.append(vec)
    return vectors


def cosine_sim(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    ma = math.sqrt(sum(x*x for x in a))
    mb = math.sqrt(sum(x*x for x in b))
    return dot / (ma * mb + 1e-9)


def test_retrieval_accuracy(chunks, label):
    """for each query, find the top 5 chunks by tf-idf similarity and check
    if any of them contain enough keywords with good context coverage."""
    print(f"\n  {label}:")
    correct, results = 0, []

    for tc in CLAUSE_QUERIES:
        query, expected = tc["q"], tc["kw"]
        corpus = list(chunks) + [query]
        vectors = compute_tfidf(corpus)
        q_vec = vectors[-1]

        scored = []
        for idx in range(len(chunks)):
            sim = cosine_sim(q_vec, vectors[idx])
            scored.append((sim, idx))
        scored.sort(reverse=True)
        top5 = scored[:5]
        top_sim = top5[0][0] if top5 else 0

        found = False
        for sim, idx in top5:
            chunk = chunks[idx]
            chunk_lower = chunk.lower()
            hits = sum(1 for kw in expected if kw in chunk_lower)

            if hits < 2:
                continue

            # check if keywords are near chunk edges (means split context, bad)
            edge_zone = 50
            edge_count = 0
            for kw in expected:
                pos = chunk_lower.find(kw)
                if pos != -1:
                    if pos < edge_zone or pos > len(chunk) - edge_zone - len(kw):
                        edge_count += 1

            if edge_count >= 2:
                continue

            if len(chunk) > 200:
                found = True
                break

        if found:
            correct += 1
        results.append({"q": query, "found": found, "sim": top_sim})

    accuracy = (correct / len(CLAUSE_QUERIES)) * 100

    print(f"  {'Query':<52} {'Match':<6} {'Score':<7}")
    print(f"  {'-'*52} {'-'*6} {'-'*7}")
    for r in results:
        print(f"  {r['q']:<52} {'YES' if r['found'] else 'NO':<6} {r['sim']:.4f}")
    print(f"\n  Result: {correct}/{len(CLAUSE_QUERIES)} = {accuracy:.1f}%")
    return accuracy


# -- chunk quality --

def print_chunk_metrics(chunks, label):
    sizes = [len(c) for c in chunks]
    broken = sum(1 for c in chunks if c and c.rstrip()[-1:] not in '.!?"\n')

    print(f"\n  {label}:")
    print(f"    Chunks: {len(chunks)} | Avg size: {round(mean(sizes))} | Stdev: {round(stdev(sizes)) if len(sizes) > 1 else 0}")
    print(f"    Range: {min(sizes)}-{max(sizes)} chars | Ends mid-sentence: {broken}/{len(chunks)}")


def main():
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PDF
    reader = PdfReader(pdf_path)
    text = "".join((page.extract_text() or "") + "\n" for page in reader.pages)
    text = text.replace("\xa0", " ")
    print(f"\n  PDF: {len(text)} chars, {len(reader.pages)} pages")

    para_chunks = paragraph_chunk(text)
    recur_chunks = recursive_chunk_text(text, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    print("\n--- CHUNK QUALITY ---")
    print_chunk_metrics(para_chunks, "Naive, no overlap")
    print_chunk_metrics(recur_chunks, "Recursive with overlap (LlamaParse)")

    print("\n--- CLAUSE RETRIEVAL ---")
    para_acc = test_retrieval_accuracy(para_chunks, "Naive, no overlap")
    recur_acc = test_retrieval_accuracy(recur_chunks, "Recursive with overlap (LlamaParse)")

    print(f"\n  Top-5 retrieval accuracy: naive {para_acc:.1f}% | recursive {recur_acc:.1f}%\n")


if __name__ == "__main__":
    main()
