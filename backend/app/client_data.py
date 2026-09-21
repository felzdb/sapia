import re
from datetime import datetime


CPF_PATTERN = re.compile(r"\b\d{3}[.\s]?\d{3}[.\s]?\d{3}[-\s]?\d{2}\b")
DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b")
NIT_PATTERN = re.compile(r"\b\d{3}\.\d{5}\.\d{2}-\d\b|\b\d{11}\b")
CURRENCY_PATTERN = re.compile(
    r"R\$\s*\d{1,3}(?:\.\d{3})*(?:,\d{2})?|\b\d+[.,]\d{2}\b"
)
COMPETENCE_PATTERN = re.compile(r"\b(0[1-9]|1[0-2])[/.-](\d{4})\b")


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" :.-")


def _normalize_cpf(value: str) -> str:
    return re.sub(r"\D", "", value)


def _valid_cpf(value: str | None) -> bool:
    if not value:
        return False

    digits = _normalize_cpf(value)

    if len(digits) != 11 or digits == digits[0] * 11:
        return False

    total = sum(int(digit) * (10 - index) for index, digit in enumerate(digits[:9]))
    first = (total * 10) % 11
    if first == 10:
        first = 0

    if first != int(digits[9]):
        return False

    total = sum(int(digit) * (11 - index) for index, digit in enumerate(digits[:10]))
    second = (total * 10) % 11
    if second == 10:
        second = 0

    return second == int(digits[10])


def _find_labeled_value(
    lines: list[str],
    labels: tuple[str, ...],
) -> str | None:
    for index, line in enumerate(lines):
        lower_line = line.lower()

        for label in labels:
            if lower_line.startswith(label):
                candidate = line[len(label):].lstrip(" :.-")
                if candidate:
                    return candidate

                if index + 1 < len(lines):
                    return lines[index + 1]

    return None


def _find_labeled_date(
    lines: list[str],
    labels: tuple[str, ...],
) -> str | None:
    value = _find_labeled_value(lines, labels)
    if value:
        match = DATE_PATTERN.search(value)
        if match:
            return match.group(0)

    for line in lines:
        lower_line = line.lower()
        if any(label in lower_line for label in labels):
            match = DATE_PATTERN.search(line)
            if match:
                return match.group(0)

    return None


def _format_date(value: str | None) -> str | None:
    if not value:
        return None

    normalized = value.replace("-", "/")
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(normalized, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue

    return value


def extract_client_data(text: str) -> dict[str, object]:
    """Extrai os campos previstos na RF6 a partir do texto do documento."""
    normalized = text.replace("\r", "")
    lines = [
        _clean_value(line)
        for line in normalized.splitlines()
        if _clean_value(line)
    ]

    name = _find_labeled_value(
        lines,
        (
            "nome do segurado",
            "nome do beneficiário",
            "nome do cliente",
            "nome completo",
            "nome",
        ),
    )

    cpf = None
    for line in lines:
        match = CPF_PATTERN.search(line)
        if match and _valid_cpf(match.group(0)):
            cpf = match.group(0)
            break

    if cpf is None:
        for match in CPF_PATTERN.finditer(normalized):
            if _valid_cpf(match.group(0)):
                cpf = match.group(0)
                break

    birth_date = _find_labeled_date(
        lines,
        ("data de nascimento", "nascimento", "dt. nascimento"),
    )

    nit_pis = _find_labeled_value(
        lines,
        (
            "nit/pis",
            "nit",
            "pis/pasep",
            "pis",
            "número do pis",
            "numero do pis",
        ),
    )
    if nit_pis:
        match = NIT_PATTERN.search(nit_pis)
        nit_pis = match.group(0) if match else nit_pis

    beneficio = _find_labeled_value(
        lines,
        (
            "número do benefício",
            "numero do benefício",
            "número benefício",
            "numero beneficio",
            "nb",
        ),
    )

    dib = _find_labeled_date(
        lines,
        (
            "data de início do benefício",
            "data de inicio do benefício",
            "dib",
            "início do benefício",
            "inicio do benefício",
        ),
    )

    competencias: list[str] = []
    for match in COMPETENCE_PATTERN.finditer(normalized):
        value = f"{match.group(1)}/{match.group(2)}"
        if value not in competencias:
            competencias.append(value)

    valor_beneficio = _find_labeled_value(
        lines,
        (
            "valor do benefício",
            "valor do beneficio",
            "valor mensal",
            "renda mensal",
            "rmi",
        ),
    )
    if valor_beneficio:
        match = CURRENCY_PATTERN.search(valor_beneficio)
        valor_beneficio = match.group(0) if match else valor_beneficio

    return {
        "nome": name,
        "cpf": cpf,
        "data_nascimento": _format_date(birth_date),
        "nit_pis": nit_pis,
        "numero_beneficio": beneficio,
        "data_inicio_beneficio": _format_date(dib),
        "competencias": competencias,
        "valor_beneficio": valor_beneficio,
    }
