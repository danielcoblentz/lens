import json
from unittest import mock

import pytest


@pytest.fixture
def handler(load_handler):
    # llamaQuery with its aws and openai clients stubbed out
    module = load_handler(
        "LlamaQuery", SESSIONS_TABLE="sessions", CHUNKS_TABLE="chunks", OPENAI_API_KEY="test"
    )

    module.sessions_table = mock.Mock()
    module.sessions_table.get_item.return_value = {"Item": {"sessionId": "s1", "status": "READY_FOR_QUERY"}}
    module.chunks_table = mock.Mock()
    module.openai_client = mock.Mock()
    module.openai_client.embeddings.create.return_value.data = [mock.Mock(embedding=[1.0, 0.0])]
    module.openai_client.chat.completions.create.return_value.choices = [
        mock.Mock(message=mock.Mock(content="answer"))
    ]
    return module


def invoke(handler, session_id="s1", query="What is the term?"):
    event = {"body": json.dumps({"sessionId": session_id, "query": query})}
    response = handler.lambda_handler(event, None)
    return response["statusCode"], json.loads(response["body"])


def chunk(i):
    return {"sessionId": "s1", "chunkId": f"chunk_{i}", "text": f"text {i}", "embedding": [1, 0]}


def test_reads_every_page_of_chunks(handler):
    # dynamodb stops a query at 1 mb and hands back LastEvaluatedKey to resume from
    handler.chunks_table.query.side_effect = [
        {"Items": [chunk(0), chunk(1)], "LastEvaluatedKey": {"chunkId": "chunk_1"}},
        {"Items": [chunk(2)], "LastEvaluatedKey": {"chunkId": "chunk_2"}},
        {"Items": [chunk(3)]},
    ]

    status, body = invoke(handler)

    assert status == 200
    assert body["metrics"]["chunks_searched"] == 4
    calls = handler.chunks_table.query.call_args_list
    assert "ExclusiveStartKey" not in calls[0].kwargs
    assert calls[1].kwargs["ExclusiveStartKey"] == {"chunkId": "chunk_1"}
    assert calls[2].kwargs["ExclusiveStartKey"] == {"chunkId": "chunk_2"}


def test_returns_404_for_an_unknown_session(handler):
    handler.sessions_table.get_item.return_value = {}

    status, body = invoke(handler)

    assert status == 404
    assert body["error"] == "Invalid sessionId"


def test_returns_409_while_the_document_is_still_processing(handler):
    handler.sessions_table.get_item.return_value = {"Item": {"sessionId": "s1", "status": "PROCESSING"}}

    status, body = invoke(handler)

    assert status == 409
    assert body == {"error": "The document is still being processed.", "status": "PROCESSING"}
    handler.openai_client.embeddings.create.assert_not_called()


def test_returns_409_with_the_parse_error_for_a_failed_document(handler):
    handler.sessions_table.get_item.return_value = {
        "Item": {"sessionId": "s1", "status": "ERROR", "error": "No text could be extracted from this PDF."}
    }

    status, body = invoke(handler)

    assert status == 409
    assert body["error"] == "No text could be extracted from this PDF."


def test_returns_404_when_the_session_has_no_chunks(handler):
    handler.chunks_table.query.return_value = {"Items": []}

    status, body = invoke(handler)

    assert status == 404
    assert body["error"] == "No chunks found"
