import json
from unittest import mock

import pytest


@pytest.fixture
def handler(load_handler):
    module = load_handler("LlamaStatus", SESSIONS_TABLE="sessions")
    module.sessions_table = mock.Mock()
    return module


def invoke(handler, session_id="s1"):
    event = {"pathParameters": {"sessionId": session_id} if session_id else None}
    response = handler.lambda_handler(event, None)
    return response["statusCode"], json.loads(response["body"])


def test_returns_the_session_status(handler):
    handler.sessions_table.get_item.return_value = {"Item": {"sessionId": "s1", "status": "PROCESSING"}}

    status, body = invoke(handler)

    assert status == 200
    assert body == {"sessionId": "s1", "status": "PROCESSING"}
    handler.sessions_table.get_item.assert_called_once_with(Key={"sessionId": "s1"})


def test_includes_the_error_message_for_a_failed_session(handler):
    handler.sessions_table.get_item.return_value = {
        "Item": {"sessionId": "s1", "status": "ERROR", "error": "No text could be extracted from this PDF."}
    }

    status, body = invoke(handler)

    assert status == 200
    assert body["error"] == "No text could be extracted from this PDF."


def test_returns_404_for_an_unknown_session(handler):
    handler.sessions_table.get_item.return_value = {}

    status, body = invoke(handler)

    assert status == 404
    assert body["error"] == "Invalid sessionId"


def test_returns_404_without_a_session_id(handler):
    status, _ = invoke(handler, session_id=None)

    assert status == 404
    handler.sessions_table.get_item.assert_not_called()
