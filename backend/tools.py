from pathlib import Path

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def save_upload_file(filename: str, content: bytes) -> Path:
    destination = UPLOAD_DIR / filename
    destination.write_bytes(content)
    return destination
