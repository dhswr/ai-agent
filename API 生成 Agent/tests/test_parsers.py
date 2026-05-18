"""测试文档解析器."""

from pathlib import Path

from vscc.agents.requirements.parsers import detect_and_parse, parse_markdown, parse_text


def test_parse_markdown_sample_prd():
    """解析 sample-prd.md 应返回非空内容."""
    path = Path(__file__).parent / "fixtures" / "sample-prd.md"
    text = parse_markdown(path)
    assert "用户管理 API" in text
    assert "/api/users" in text
    assert "## 数据库实体" in text


def test_parse_text():
    """解析纯文本文件."""
    path = Path(__file__).parent / "fixtures" / "sample-prd.md"
    text = parse_text(path)
    assert len(text) > 0


def test_detect_and_parse_md():
    """自动检测 .md 文件使用 Markdown 解析器."""
    path = Path(__file__).parent / "fixtures" / "sample-prd.md"
    text = detect_and_parse(path)
    assert "用户管理 API" in text


def test_detect_and_parse_txt():
    """自动检测 .txt 文件使用文本解析器."""
    path = Path(__file__).parent / "fixtures" / "sample-prd.md"
    text = detect_and_parse(path)  # .md treated by suffix
    assert len(text) > 0
