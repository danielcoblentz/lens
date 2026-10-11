## Architecture

Three independent Lambda functions, each deployed as its own zip:

- `LlamaGet/lambda_function.py` - creates a session, returns a presigned S3 upload URL.
- `LlamaParse/lambda_function.py` - triggered by the S3 upload event, extracts and chunks the PDF text, embeds each chunk, writes the chunks to DynamoDB.
- `LlamaQuery/lambda_function.py` - embeds a question, ranks the stored chunks by cosine similarity, and prompts the LLM with the highest scoring ones.

The pure logic is kept out of the handlers so it can be tested without AWS or OpenAI:

- `LlamaParse/chunking.py` - `recursive_chunk_text`.
- `LlamaQuery/retrieval.py` - `cosine_similarity` and `rank_chunks`.

## Prerequisites

- Python 3.10+
- An S3 bucket for uploads, two DynamoDB tables, and IAM roles allowing each function to reach them
- An OpenAI API key

## Dependencies

`LlamaGet` only needs boto3, which the Lambda runtime already provides. The other two
need their dependencies vendored into the deployment package:

```bash
pip install PyPDF2 openai -t LlamaParse
pip install -r LlamaQuery/requirements.txt -t LlamaQuery
```

## Environment Variables

| Function | Variables |
|----------|-----------|
| LlamaGet | `BUCKET_NAME`, `TABLE_NAME` |
| LlamaParse | `BUCKET_NAME`, `SESSIONS_TABLE`, `CHUNKS_TABLE`, `OPENAI_API_KEY` |
| LlamaQuery | `SESSIONS_TABLE`, `CHUNKS_TABLE`, `OPENAI_API_KEY` |

`TABLE_NAME` and `SESSIONS_TABLE` refer to the same sessions table; the two functions
just read it under different names. `OPENAI_API_KEY` is read by the OpenAI client
itself rather than by the handler code.

The embedding model (`text-embedding-3-small`) and the chat model (`gpt-4o-mini`) are
hardcoded in the handlers, not configurable through the environment.

Copy `.env.example` to `.env` for local use. `.env` is git-ignored; never commit keys.

## Data Model (DynamoDB)

Sessions table, partition key `sessionId`:

- `sessionId` (string)
- `status` - `AWAITING_UPLOAD` on creation, `READY_FOR_QUERY` once parsing finishes
- `createdAt` - ISO 8601 timestamp
- `s3Key` - `uploads/{sessionId}.pdf`

Chunks table, partition key `sessionId` and sort key `chunkId`:

- `chunkId` - `chunk_0`, `chunk_1`, and so on
- `text` - the chunk body
- `embedding` - list of `Decimal`, converted back to float when scoring
- `order` - the chunk index

## API

Both routes are POST, fronted by API Gateway.

`POST /llamaGet` takes no body.

```json
{ "sessionId": "…", "uploadUrl": "https://…" }
```

`POST /query`:

```json
{ "sessionId": "…", "query": "What is the termination clause?" }
```

```json
{ "sessionId": "…", "answer": "…", "metrics": { "embedding_time_ms": 0, "similarity_search_time_ms": 0, "chunks_searched": 0, "llm_time_ms": 0, "total_time_ms": 0, "top_chunk_similarity": 0 } }
```

Returns 404 if the session is unknown or has no chunks yet.

## Workflows

Upload: `POST /llamaGet` creates the session and returns a presigned URL, the browser
PUTs the PDF straight to S3, and the object-created event on the `uploads/` prefix
triggers LlamaParse, which flips the session to `READY_FOR_QUERY`.

Query: `POST /query` embeds the question, scores every chunk stored for the session,
and sends the top five to the LLM.

## Deployment

`template.yaml` in the repo root is a SAM template covering all three functions, the
bucket, both tables, the IAM roles, the API Gateway routes, and the S3 notification.

```bash
sam build
sam deploy --guided
```

It asks for `UploadBucketName` and `OpenAIApiKey`, and outputs `ApiBaseUrl` for the
frontend's `REACT_APP_API_BASE`.

## Tests

The chunking and retrieval modules are covered by pytest and need no AWS credentials:

```bash
pip install pytest
python -m pytest tests
```

## Notes

- Keep presigned URL expiry short; it is currently one hour.
- LlamaParse embeds one chunk per request, so a large PDF means a lot of sequential calls.
- Parsing is not idempotent - re-uploading the same key rewrites the chunks.
