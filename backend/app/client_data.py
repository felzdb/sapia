import re
from datetime import datetime


CPF_PATTERN = re.compile(r"\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}\b")
DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b")


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :.-")


def extract_client_data(text: str) -> dict[str, str | None]:
    """Extrai dados básicos do cliente a partir do texto já extraído do PDF."""
    normalized = text.replace("\r", "")
    lines = [_clean_value(line) for line in normalized.splitlines() if _clean_value(line)]

    name = None
    cpf = None
    birth_date = None

    name_labels = (
        "nome do segurado",
        "nome do beneficiário",
        "nome do cliente",
        "nome completo",
        "nome",
    )

    for line in lines:
        lower_line = line.lower()

        if name is None:
            for label in name_labels:
                if lower_line.startswith(label):
                    candidate = line[len(label):].lstrip(" :")
                    if candidate:
                        name = candidate
                        break

        if cpf is None:
            cpf_match = CPF_PATTERN.search(line)
            if cpf_match:
                cpf = cpf_match.group(0)

        if birth_date is None and any(
            label in lower_line
            for label in ("data de nascimento", "nascimento", "dt. nascimento")
        ):
            date_match = DATE_PATTERN.search(line)
            if date_match:
                birth_date = date_match.group(0)

    if cpf is None:
        cpf_match = CPF_PATTERN.search(normalized)
        if cpf_match:
            cpf = cpf_match.group(0)

    if birth_date is None:
        for line in lines:
            if "nascimento" in line.lower():
                date_match = DATE_PATTERN.search(line)
                if date_match:
                    birth_date = date_match.group(0)
                    break

    if birth_date:
        try:
            birth_date = datetime.strptime(birth_date, "%d/%m/%Y").strftime("%d/%m/%Y")
        except ValueError:
            pass

    return {
        "nome": name,
        "cpf": cpf,
        "data_nascimento": birth_date,
    }
