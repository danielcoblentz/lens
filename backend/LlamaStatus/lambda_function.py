import json
import os
import boto3

dynamodb_resource = boto3.resource("dynamodb")
sessions_table = dynamodb_resource.Table(os.environ["SESSIONS_TABLE"])

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET, OPTIONS"
}


def lambda_handler(event, context):
    # the frontend polls this after uploading, until parsing reaches a terminal state
    session_id = (event.get("pathParameters") or {}).get("sessionId")
    session = sessions_table.get_item(Key={"sessionId": session_id}) if session_id else {}

    if "Item" not in session:
        return {"statusCode": 404, "headers": CORS_HEADERS,
                "body": json.dumps({"error": "Invalid sessionId"})}

    item = session["Item"]
    body = {"sessionId": session_id, "status": item["status"]}
    if "error" in item:
        body["error"] = item["error"]

    return {"statusCode": 200, "headers": CORS_HEADERS, "body": json.dumps(body)}
