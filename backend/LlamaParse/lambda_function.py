import json
import boto3
import os
from decimal import Decimal
from PyPDF2 import PdfReader
from openai import OpenAI

from chunking import recursive_chunk_text

s3_client = boto3.client("s3")
dynamodb_resource = boto3.resource("dynamodb")

sessions_table = dynamodb_resource.Table(os.environ["SESSIONS_TABLE"])
chunks_table = dynamodb_resource.Table(os.environ["CHUNKS_TABLE"])
pdf_bucket_name = os.environ["BUCKET_NAME"]

openai_client = OpenAI()


def generate_embedding(text):
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def lambda_handler(event, context):
    # triggered by s3 upload event
    s3_event = event["Records"][0]
    source_bucket = s3_event["s3"]["bucket"]["name"]
    uploaded_key = s3_event["s3"]["object"]["key"]

    file_name = uploaded_key.split("/")[-1]
    session_id = file_name.replace(".pdf", "")

    # download and extract text from the pdf
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

    # mark session as ready so llamaQuery knows it can accept questions
    sessions_table.update_item(
        Key={"sessionId": session_id},
        UpdateExpression="SET #s = :status",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":status": "READY_FOR_QUERY"}
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "sessionId": session_id,
            "chunksCreated": len(text_chunks)
        })
    }
