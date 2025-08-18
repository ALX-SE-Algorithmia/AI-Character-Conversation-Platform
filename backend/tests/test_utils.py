from pathlib import Path
from tempfile import TemporaryDirectory

from backend.utils.faiss_helper import ensure_vector_dir


def test_ensure_vector_dir_creates_path():
    with TemporaryDirectory() as tmp:
        p = ensure_vector_dir(str(Path(tmp) / "vec"))
        assert p.exists() and p.is_dir()
