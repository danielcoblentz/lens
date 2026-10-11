# scripts

Checks for retrieval quality.

```bash
pip install -r scripts/requirements.txt
```

## compare_chunking.py

Compares naive chunking with no overlap against the recursive chunker in `backend/LlamaParse/chunking.py`.
It runs 32 clause questions against `samples/sample_legal_contract.pdf` and ranks chunks with TF-IDF, so it needs no API key.
A question counts as answered when one of the top 5 chunks holds at least two expected keywords away from the chunk edges.

```bash
python scripts/compare_chunking.py
```

On the sample contract the recursive chunker answers 32 of 32 questions and the naive chunker answers 31 of 32.
