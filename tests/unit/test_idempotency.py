from src.common.crypto import sha256_bytes

def test_content_hash_is_deterministic():
    doc_id = "doc-123"
    file_bytes = b"same bytes every time"
    h1 = sha256_bytes(b"|".join([doc_id.encode("utf-8"), file_bytes]))
    h2 = sha256_bytes(b"|".join([doc_id.encode("utf-8"), file_bytes]))
    assert h1 == h2
