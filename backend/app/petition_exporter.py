
from io import BytesIO
from pathlib import Path
import re

import fitz
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt


SECTION_TITLES = {
    "QUALIFICAÇÃO",
    "DOS FATOS",
    "DO DIREITO",
    "DOS PEDIDOS",
    "PARTICULARIDADES DO CASO",
    "DO VALOR DA CAUSA",
}

DATE_PATTERN = re.compile(
    r"^.+,\s*\d{1,2} de "
    r"(?:janeiro|fevereiro|março|abril|maio|junho|"
    r"julho|agosto|setembro|outubro|novembro|dezembro)"
    r" de \d{4}\.$",
    flags=re.IGNORECASE,
)


def is_heading(text: str, first_paragraph: bool = False) -> bool:
    """Identifica os títulos principais da petição."""
    return (
        first_paragraph
        or text in SECTION_TITLES
        or text.startswith("PETIÇÃO INICIAL")
    )


def is_closing(text: str) -> bool:
    """Identifica as linhas do encerramento da petição."""
    return (
        text.casefold() in {"termos em que,", "pede deferimento."}
        or bool(DATE_PATTERN.fullmatch(text))
    )


def export_petition_docx(content: str) -> bytes:
    """Gera documento Word com formatação jurídica."""

    document = Document()
    section = document.sections[0]

    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(3)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(3)
    section.right_margin = Cm(2)

    normal_style = document.styles["Normal"]
    normal_style.font.name = "Arial"
    normal_style.font.size = Pt(12)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(12)

    paragraphs = [
        line.strip()
        for line in content.splitlines()
        if line.strip()
    ]

    for index, text in enumerate(paragraphs):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.line_spacing = 1.5

        if is_heading(text, index == 0):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.space_before = (
                Pt(24) if index > 0 else Pt(0)
            )
            paragraph.paragraph_format.space_after = Pt(18)

            run = paragraph.add_run(text)
            run.bold = True

        elif is_closing(text):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Cm(0)
            paragraph.paragraph_format.space_after = Pt(12)

            if text.casefold() == "termos em que,":
                paragraph.paragraph_format.keep_with_next = True

            paragraph.add_run(text)


        else:
            paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            paragraph.paragraph_format.first_line_indent = Cm(1.25)
            paragraph.paragraph_format.space_after = Pt(12)

            # Evita separar a introdução dos primeiros pedidos.
            if index > 0 and paragraphs[index - 1] == "DOS PEDIDOS":
                paragraph.paragraph_format.keep_with_next = True

            # Mantém o primeiro pedido junto ao segundo.
            if (
                text.startswith("1.")
                and index > 0
                and "Diante do exposto" in paragraphs[index - 1]
            ):
                paragraph.paragraph_format.keep_with_next = True

            paragraph.add_run(text)


    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def export_petition_pdf(content: str) -> bytes:
    """Gera PDF com quebra de linhas e paginação automática."""

    fonts_directory = Path(__file__).resolve().parent / "fonts"
    font_regular = fonts_directory / "LiberationSans-Regular.ttf"
    font_bold = fonts_directory / "LiberationSans-Bold.ttf"

    if not font_regular.is_file() or not font_bold.is_file():
        raise FileNotFoundError(
            "Fontes Liberation Sans não encontradas na pasta app/fonts."
        )

    regular_font = fitz.Font(fontfile=str(font_regular))
    bold_font = fitz.Font(fontfile=str(font_bold))

    page_width = 595.28
    page_height = 841.89

    left_margin = 85.04
    right_margin = 56.69
    top_margin = 85.04
    bottom_margin = 56.69

    available_width = page_width - left_margin - right_margin
    bottom_limit = page_height - bottom_margin

    font_size = 12
    line_height = 18
    paragraph_spacing = 12
    heading_spacing_before = 24
    heading_spacing_after = 18
    first_line_indent = 35.43

    pdf = fitz.open()

    try:
        def new_page():
            page = pdf.new_page(
                width=page_width,
                height=page_height,
            )

            page.insert_font(
                fontname="LiberationRegular",
                fontfile=str(font_regular),
            )
            page.insert_font(
                fontname="LiberationBold",
                fontfile=str(font_bold),
            )

            return page

        def wrap_text(text, font, indent=0):
            """Quebra o texto por palavras, respeitando as margens."""

            words = text.split()
            lines = []
            current_line = ""

            for word in words:
                max_width = available_width

                if not lines:
                    max_width -= indent

                candidate = f"{current_line} {word}".strip()

                if font.text_length(
                    candidate,
                    fontsize=font_size,
                ) <= max_width:
                    current_line = candidate
                    continue

                if current_line:
                    lines.append(current_line)
                    current_line = ""

                if font.text_length(
                    word,
                    fontsize=font_size,
                ) <= available_width:
                    current_line = word
                    continue

                for character in word:
                    candidate = current_line + character

                    if (
                        font.text_length(
                            candidate,
                            fontsize=font_size,
                        ) > available_width
                        and current_line
                    ):
                        lines.append(current_line)
                        current_line = character
                    else:
                        current_line = candidate

            if current_line:
                lines.append(current_line)

            return lines

        paragraphs = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        page = new_page()
        y = top_margin

        for index, paragraph in enumerate(paragraphs):
            heading = is_heading(
                paragraph,
                first_paragraph=(index == 0),
            )
            closing = is_closing(paragraph)

            font = bold_font if heading else regular_font
            font_name = (
                "LiberationBold" if heading else "LiberationRegular"
            )

            indent = (
                0 if heading or closing else first_line_indent
            )

            lines = wrap_text(paragraph, font, indent)

            if not lines:
                continue

            # Evita título isolado no fim da página.

            # Evita títulos isolados e mantém o início dos pedidos
            # junto ao título da seção.
            if heading and index > 0:
                required_height = (
                    heading_spacing_before
                    + len(lines) * line_height
                    + heading_spacing_after
                    + line_height
                    + paragraph_spacing
                )

                if paragraph == "DOS PEDIDOS":
                    # Reserva espaço para o texto introdutório
                    # e os primeiros itens da lista de pedidos.
                    for next_paragraph in paragraphs[index + 1:index + 4]:
                        next_lines = wrap_text(
                            next_paragraph,
                            regular_font,
                            first_line_indent,
                        )

                        required_height += (
                            len(next_lines) * line_height
                            + paragraph_spacing
                        )

                if y + required_height > bottom_limit:
                    page = new_page()
                    y = top_margin
                else:
                    y += heading_spacing_before


            # Tenta manter as linhas do encerramento juntas.
            if paragraph.casefold() == "termos em que,":
                closing_lines = 0

                for next_paragraph in paragraphs[index:]:
                    if not is_closing(next_paragraph):
                        break

                    next_lines = wrap_text(
                        next_paragraph,
                        regular_font,
                        0,
                    )

                    closing_lines += len(next_lines)

                required_height = (
                    closing_lines * line_height
                    + closing_lines * paragraph_spacing
                )

                if y + required_height > bottom_limit:
                    page = new_page()
                    y = top_margin

            for line_index, line in enumerate(lines):
                if y + line_height > bottom_limit:
                    page = new_page()
                    y = top_margin

                if heading or closing:
                    text_width = font.text_length(
                        line,
                        fontsize=font_size,
                    )

                    x = left_margin + (
                        available_width - text_width
                    ) / 2

                else:
                    x = left_margin

                    if line_index == 0:
                        x += first_line_indent

                should_justify = (
                    not heading
                    and not closing
                    and line_index < len(lines) - 1
                    and " " in line
                )

                if should_justify:
                    words = line.split()

                    text_width = sum(
                        font.text_length(
                            word,
                            fontsize=font_size,
                        )
                        for word in words
                    )

                    line_width = available_width

                    if line_index == 0:
                        line_width -= first_line_indent

                    space_width = (
                        line_width - text_width
                    ) / (len(words) - 1)

                    current_x = x

                    for word in words:
                        page.insert_text(
                            (current_x, y + font_size),
                            word,
                            fontname=font_name,
                            fontsize=font_size,
                        )

                        current_x += (
                            font.text_length(
                                word,
                                fontsize=font_size,
                            )
                            + space_width
                        )

                else:
                    page.insert_text(
                        (x, y + font_size),
                        line,
                        fontname=font_name,
                        fontsize=font_size,
                    )

                y += line_height

            if heading:
                y += heading_spacing_after
            else:
                y += paragraph_spacing

        return pdf.tobytes()

    finally:
        pdf.close()
