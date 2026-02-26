from app.services.text_cleanup import clean_text_for_epub_body


def test_clean_text_removes_page_block_and_filename() -> None:
    raw = """페이지 25
    25
    260215 주일말씀.hwp
    - 25 -

    본문입니다.
    """

    cleaned = clean_text_for_epub_body(raw)
    assert "페이지 25" not in cleaned
    assert "260215 주일말씀.hwp" not in cleaned
    assert "- 25 -" not in cleaned
    assert cleaned == "본문입니다."


def test_clean_text_removes_watermark_and_banner_lines() -> None:
    raw = """변환된 문서
    PdfToEpub Converter
    이 자료는 저작권에 의해 보호됩니다.
    다음에서 발췌

    Hello
    """

    cleaned = clean_text_for_epub_body(raw)
    assert "PdfToEpub" not in cleaned
    assert "저작권" not in cleaned
    assert "다음에서 발췌" not in cleaned
    assert cleaned.endswith("Hello")


def test_clean_text_keeps_numbers_when_not_page_artifact() -> None:
    raw = """25
    본문
    """

    cleaned = clean_text_for_epub_body(raw)
    assert cleaned == "25\n본문"
