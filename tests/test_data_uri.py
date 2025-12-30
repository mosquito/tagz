import base64
import pytest
from tagz import data_uri, open_data_uri


def test_data_uri():
    data = b"hello world"
    uri = data_uri(data, media_type="text/plain")
    assert uri.startswith("data:text/plain;base64,")
    assert uri.endswith("aGVsbG8gd29ybGQ=")


def test_open_data_url(tmp_path):
    # Create a temporary file with known content
    file_path = tmp_path / "test.txt"
    content = b"file content"
    file_path.write_bytes(content)
    uri = open_data_uri(str(file_path))
    assert uri.startswith("data:text/plain;base64,")
    # Check the base64-encoded content
    encoded = base64.b64encode(content).decode("ascii")
    assert uri.endswith(encoded)


def test_open_data_url_with_custom_media_type(tmp_path):
    file_path = tmp_path / "test.bin"
    content = b"binary\x00data"
    file_path.write_bytes(content)
    uri = open_data_uri(str(file_path), media_type="application/x-custom")
    assert uri.startswith("data:application/x-custom;base64,")
    encoded = base64.b64encode(content).decode("ascii")
    assert uri.endswith(encoded)
