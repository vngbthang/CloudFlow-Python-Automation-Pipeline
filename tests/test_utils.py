from hashlib import sha256

from src.utils import calculate_file_hash


def test_calculate_file_hash_returns_stable_sha256_hash(tmp_path):
    file_path = tmp_path / "sample.csv"
    content = b"order_id,amount\n1,100\n"
    file_path.write_bytes(content)

    first_hash = calculate_file_hash(file_path)
    second_hash = calculate_file_hash(file_path)

    assert first_hash == second_hash
    assert first_hash == sha256(content).hexdigest()
    assert len(first_hash) == 64
