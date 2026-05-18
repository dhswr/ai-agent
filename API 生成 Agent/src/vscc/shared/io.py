"""文件系统辅助工具."""

from pathlib import Path


def read_text(file_path: Path) -> str:
    return file_path.read_text(encoding="utf-8")


def write_text(file_path: Path, content: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def write_json(file_path: Path, content: str) -> None:
    write_text(file_path, content)


def ensure_dir(dir_path: Path) -> Path:
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
