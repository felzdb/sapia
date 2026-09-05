from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz


class PDFReadError(Exception):
    """Erro lançado quando um PDF não pode ser lido."""


@dataclass(frozen=True)
class PDFReading:
    """Resultado da leitura de um documento PDF."""

    text: str
    page_count: int
    pages_without_text: tuple[int, ...]


def read_pdf_document(file_path: str | Path) -> PDFReading:
    """Extrai o texto de todas as páginas utilizando PyMuPDF."""

    path = Path(file_path)

    if not path.is_file():
        raise PDFReadError("O arquivo PDF não foi encontrado.")

    try:
        with fitz.open(path) as document:
            if document.needs_pass:
                raise PDFReadError("O PDF está protegido por senha.")

            page_texts: list[str] = []
            pages_without_text: list[int] = []

            for page_number, page in enumerate(document, start=1):
                blocks = page.get_text("blocks", sort=True)
                page_text = "\n".join(
                    block[4].strip()
                    for block in blocks
                    if block[4].strip()
                )

                if not page_text:
                    pages_without_text.append(page_number)

                page_texts.append(page_text)

            return PDFReading(
                text="\n\f\n".join(page_texts),
                page_count=document.page_count,
                pages_without_text=tuple(pages_without_text),
            )
    except PDFReadError:
        raise
    except (fitz.FileDataError, RuntimeError, ValueError) as exc:
        raise PDFReadError(
            "O arquivo enviado não é um PDF legível."
        ) from exc
