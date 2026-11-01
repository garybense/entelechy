import json

from entelechy_api.engine.retain.reprocess import _content_item


def test_content_item_restores_retain_params():
    row = {
        "id": "doc1",
        "original_text": "hello",
        "retain_params": json.dumps({"context": "c", "event_date": "2025-01-02T03:04:05+00:00", "metadata": {"k": "v"}}),
        "tags": ["a"],
    }
    item = _content_item(row)
    assert item["document_id"] == "doc1" and item["content"] == "hello"
    assert item["context"] == "c" and item["metadata"] == {"k": "v"} and item["tags"] == ["a"]
    assert item["event_date"].year == 2025


def test_content_item_without_params():
    item = _content_item({"id": "d", "original_text": "t", "retain_params": None, "tags": []})
    assert item == {"content": "t", "document_id": "d"}
