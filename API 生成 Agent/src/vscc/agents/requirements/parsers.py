"""文档解析器 —— 支持 Markdown, TXT, PDF."""

from pathlib import Path


def parse_markdown(file_path: Path) -> str:
    """读取 MD 文件为纯文本."""
    return file_path.read_text(encoding="utf-8")


def parse_text(file_path: Path) -> str:
    """读取纯文本文件."""
    return file_path.read_text(encoding="utf-8")


def parse_pdf(file_path: Path) -> str:
    """使用 PyMuPDF 提取 PDF 文本."""
    import fitz

    doc = fitz.open(str(file_path))
    pages = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            pages.append(text)
    doc.close()
    return "\n\n".join(pages)


def detect_and_parse(file_path: Path) -> str:
    """根据文件后缀自动选择解析器."""
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return parse_pdf(file_path)
    elif suffix in (".md", ".markdown"):
        return parse_markdown(file_path)
    else:
        return parse_text(file_path)
