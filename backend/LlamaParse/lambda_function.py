import json
import logging
import boto3
import os
from decimal import Decimal
from pypdf import PdfReader
from openai import OpenAI

from chunking import recursive_chunk_text

s3_client = boto3.client("s3")
dynamodb_resource = boto3.resource("dynamodb")

sessions_table = dynamodb_resource.Table(os.environ["SESSIONS_TABLE"])
chunks_table = dynamodb_resource.Table(os.environ["CHUNKS_TABLE"])
pdf_bucket_name = os.environ["BUCKET_NAME"]

openai_client = OpenAI()

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_embedding(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def set_session_status(session_id, status, error=None):
    update = "SET #s = :status"
    names = {"#s": "status"}
    values = {":status": status}
    if error is not None:
        update += ", #e = :error"
        names["#e"] = "error"
        values[":error"] = error
    sessions_table.update_item(
        Key={"sessionId": session_id},
        UpdateExpression=update,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values
    )


def lambda_handler(event, context):
    # triggered by s3 upload event
    s3_event = event["Records"][0]
    source_bucket = s3_event["s3"]["bucket"]["name"]
    uploaded_key = s3_event["s3"]["object"]["key"]

    file_name = uploaded_key.split("/")[-1]
    session_id = file_name.replace(".pdf", "")

    # the frontend polls this status, so it has to land in a terminal state either way
    set_session_status(session_id, "PROCESSING")
    try:
        chunk_count = parse_document(session_id, source_bucket, uploaded_key)
    except Exception:
        logger.exception("parsing failed for session %s", session_id)
        set_session_status(session_id, "ERROR", error="The document could not be processed.")
        raise

    # a scanned pdf has no text layer, so there is nothing to search
    if chunk_count == 0:
        set_session_status(session_id, "ERROR", error="No text could be extracted from this PDF.")
    else:
        # llamaQuery only answers once the session is ready
        set_session_status(session_id, "READY_FOR_QUERY")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "sessionId": session_id,
            "chunksCreated": chunk_count
        })
    }


def parse_document(session_id, source_bucket, uploaded_key):
    local_path = f"/tmp/{session_id}.pdf"
    s3_client.download_file(source_bucket, uploaded_key, local_path)

    pdf_reader = PdfReader(local_path)
    extracted_text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            extracted_text += page_text + "\n"

    # chunk the text and generate embeddings for each chunk
    text_chunks = recursive_chunk_text(extracted_text, chunk_size=800, chunk_overlap=100)

    for i, chunk_text in enumerate(text_chunks):
        embedding = generate_embedding(chunk_text)
        embedding_decimals = [Decimal(str(v)) for v in embedding]

        chunks_table.put_item(Item={
            "sessionId": session_id,
            "chunkId": f"chunk_{i}",
            "text": chunk_text,
            "embedding": embedding_decimals,
            "order": i
        })

    return len(text_chunks)
