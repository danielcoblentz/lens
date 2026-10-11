import json
import boto3
import uuid
import os
from datetime import datetime

s3_client = boto3.client("s3")
dynamodb_resource = boto3.resource("dynamodb")

pdf_upload_bucket = os.environ["BUCKET_NAME"]
sessions_table_name = os.environ["TABLE_NAME"]
sessions_table = dynamodb_resource.Table(sessions_table_name)


def lambda_handler(event, context):
    new_session_id = str(uuid.uuid4())
    s3_object_key = f"uploads/{new_session_id}.pdf"

    # presigned url lets the frontend upload directly to s3
    presigned_upload_url = s3_client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": pdf_upload_bucket,
            "Key": s3_object_key,
            "ContentType": "application/pdf"
        },
        ExpiresIn=3600
    )

    # create session record so llamaParse can find it after upload
    sessions_table.put_item(
        Item={
            "sessionId": new_session_id,
            "status": "AWAITING_UPLOAD",
            "createdAt": datetime.utcnow().isoformat(),
            "s3Key": s3_object_key
        }
    )

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST, OPTIONS"
        },
        "body": json.dumps({
            "sessionId": new_session_id,
            "uploadUrl": presigned_upload_url
        })
    }
