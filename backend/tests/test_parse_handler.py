from unittest import mock

import pytest

EVENT = {"Records": [{"s3": {"bucket": {"name": "uploads"}, "object": {"key": "uploads/s1.pdf"}}}]}


@pytest.fixture
def handler(load_handler):
    # llamaParse with s3, dynamodb, openai, and the pdf reader stubbed out
    module = load_handler(
        "LlamaParse",
        BUCKET_NAME="uploads",
        SESSIONS_TABLE="sessions",
        CHUNKS_TABLE="chunks",
        OPENAI_API_KEY="test",
    )
    module.s3_client = mock.Mock()
    module.sessions_table = mock.Mock()
    module.chunks_table = mock.Mock()
    module.openai_client = mock.Mock()
    module.openai_client.embeddings.create.return_value.data = [mock.Mock(embedding=[0.5, 0.5])]
    return module


def with_pages(handler, *texts):
    pages = [mock.Mock(**{"extract_text.return_value": text}) for text in texts]
    handler.PdfReader = mock.Mock(return_value=mock.Mock(pages=pages))


def statuses(handler):
    return [c.kwargs["ExpressionAttributeValues"][":status"] for c in handler.sessions_table.update_item.call_args_list]


def test_marks_the_session_processing_then_ready(handler):
    with_pages(handler, "The term of this agreement is one year.")

    handler.lambda_handler(EVENT, None)

    assert statuses(handler) == ["PROCESSING", "READY_FOR_QUERY"]
    handler.chunks_table.put_item.assert_called_once()


def test_marks_the_session_errored_and_reraises_when_parsing_fails(handler):
    handler.PdfReader = mock.Mock(side_effect=ValueError("corrupt pdf"))

    with pytest.raises(ValueError):
        handler.lambda_handler(EVENT, None)

    assert statuses(handler) == ["PROCESSING", "ERROR"]
    last = handler.sessions_table.update_item.call_args.kwargs
    assert last["ExpressionAttributeNames"] == {"#s": "status", "#e": "error"}
    assert last["ExpressionAttributeValues"][":error"] == "The document could not be processed."


def test_marks_a_pdf_with_no_text_as_errored(handler):
    with_pages(handler, "", None)

    handler.lambda_handler(EVENT, None)

    assert statuses(handler) == ["PROCESSING", "ERROR"]
    handler.chunks_table.put_item.assert_not_called()
