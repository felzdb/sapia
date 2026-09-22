from dataclasses import dataclass
import unicodedata


BENEFIT_TYPES = (
    "APOSENTADORIA_IDADE",
    "APOSENTADORIA_TEMPO_CONTRIBUICAO",
    "APOSENTADORIA_INCAPACIDADE",
    "AUXILIO_INCAPACIDADE_TEMPORARIA",
    "AUXILIO_ACIDENTE",
    "PENSAO_MORTE",
    "SALARIO_MATERNIDADE",
    "BPC_IDOSO",
    "BPC_DEFICIENCIA",
    "OUTRO",
    "NAO_IDENTIFICADO",
)


@dataclass(frozen=True)
class BenefitIdentification:
    benefit_type: str
    confidence: float


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)

    without_accents = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    )

    return without_accents.upper()


def identify_benefit(text: str) -> BenefitIdentification:
    normalized_text = normalize_text(text)

    if "APOSENTADORIA POR IDADE" in normalized_text:
        return BenefitIdentification(
            benefit_type="APOSENTADORIA_IDADE",
            confidence=0.95,
        )

    if "APOSENTADORIA POR TEMPO DE CONTRIBUICAO" in normalized_text:
        return BenefitIdentification(
            benefit_type="APOSENTADORIA_TEMPO_CONTRIBUICAO",
            confidence=0.95,
        )

    if (
        "APOSENTADORIA POR INCAPACIDADE PERMANENTE" in normalized_text
        or "APOSENTADORIA POR INVALIDEZ" in normalized_text
    ):
        return BenefitIdentification(
            benefit_type="APOSENTADORIA_INCAPACIDADE",
            confidence=0.95,
        )

    if (
        "AUXILIO POR INCAPACIDADE TEMPORARIA" in normalized_text
        or "AUXILIO-DOENCA" in normalized_text
        or "AUXILIO DOENCA" in normalized_text
    ):
        return BenefitIdentification(
            benefit_type="AUXILIO_INCAPACIDADE_TEMPORARIA",
            confidence=0.95,
        )

    if (
        "AUXILIO-ACIDENTE" in normalized_text
        or "AUXILIO ACIDENTE" in normalized_text
    ):
        return BenefitIdentification(
            benefit_type="AUXILIO_ACIDENTE",
            confidence=0.95,
        )

    if "PENSAO POR MORTE" in normalized_text:
        return BenefitIdentification(
            benefit_type="PENSAO_MORTE",
            confidence=0.95,
        )

    if (
        "SALARIO-MATERNIDADE" in normalized_text
        or "SALARIO MATERNIDADE" in normalized_text
    ):
        return BenefitIdentification(
            benefit_type="SALARIO_MATERNIDADE",
            confidence=0.95,
        )

    if (
        "BPC IDOSO" in normalized_text
        or "BENEFICIO ASSISTENCIAL AO IDOSO" in normalized_text
    ):
        return BenefitIdentification(
            benefit_type="BPC_IDOSO",
            confidence=0.95,
        )

    if (
        "BPC DEFICIENCIA" in normalized_text
        or "BPC PESSOA COM DEFICIENCIA" in normalized_text
        or "BENEFICIO ASSISTENCIAL A PESSOA COM DEFICIENCIA"
        in normalized_text
    ):
        return BenefitIdentification(
            benefit_type="BPC_DEFICIENCIA",
            confidence=0.95,
        )

    return BenefitIdentification(
        benefit_type="NAO_IDENTIFICADO",
        confidence=0.0,
    )
