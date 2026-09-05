import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz

from app.pdf_reader import PDFReadError, read_pdf_document


class PDFReaderTests(unittest.TestCase):
    def test_extracts_text_and_counts_pages(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "document.pdf"

            with fitz.open() as document:
                first_page = document.new_page()
                first_page.insert_text((72, 72), "Primeira pagina")
                document.new_page()
                document.save(path)

            reading = read_pdf_document(path)

            self.assertIn("Primeira pagina", reading.text)
            self.assertEqual(reading.page_count, 2)
            self.assertEqual(reading.pages_without_text, (2,))

    def test_rejects_missing_file(self):
        with self.assertRaisesRegex(
            PDFReadError,
            "não foi encontrado",
        ):
            read_pdf_document("arquivo-inexistente.pdf")

    def test_rejects_corrupted_pdf(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corrupted.pdf"
            path.write_bytes(b"%PDF-conteudo-invalido")

            with self.assertRaisesRegex(PDFReadError, "não é um PDF legível"):
                read_pdf_document(path)


if __name__ == "__main__":
    unittest.main()
