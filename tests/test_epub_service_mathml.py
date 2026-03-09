import io
import zipfile

from app.services.epub_service import Chapter, EpubGenerator
from app.services.epub_validator import validate_epub_bytes


def test_epub_generator_marks_mathml_documents_and_preserves_math_tags() -> None:
    generator = EpubGenerator(language="ko")
    chapter = Chapter(
        title="Math",
        file_name="chapter1.xhtml",
        content=(
            "<h1>Math</h1>"
            '<p><math xmlns="http://www.w3.org/1998/Math/MathML" display="inline">'
            "<msup><mi>x</mi><mn>2</mn></msup>"
            "</math></p>"
        ),
    )

    epub_bytes = generator.create_epub_bytes(
        title="Math Book",
        author="",
        chapters=[chapter],
        uid="math-book",
    )

    archive = zipfile.ZipFile(io.BytesIO(epub_bytes))
    opf_text = archive.read("EPUB/content.opf").decode("utf-8")
    chapter_text = archive.read("EPUB/chapter1.xhtml").decode("utf-8")
    validation = validate_epub_bytes(epub_bytes)

    assert 'properties="mathml"' in opf_text
    assert '<math xmlns="http://www.w3.org/1998/Math/MathML"' in chapter_text
    assert not any(issue.code == "MATHML_PROPERTY_MISSING" for issue in validation.warnings)
