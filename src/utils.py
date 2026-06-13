from hashlib import sha256
from pathlib import Path


def calculate_file_hash(file_path: str | Path) -> str:
    file_path = Path(file_path)
    hasher = sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()
