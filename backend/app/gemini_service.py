import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from .schemas import ClientDataResponse


load_dotenv()


class GeminiDocumentAnalysis(BaseModel):
    benefit_type: str
    benefit_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
    dados_cliente: ClientDataResponse


def analyze_document_text(
    text: str,
) -> GeminiDocumentAnalysis:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada."
        )

    client = genai.Client(
        api_key=api_key
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=(
            "Analise o conteúdo de um documento previdenciário do INSS. "
            "Extraia somente informações que estejam realmente presentes "
            "no documento. Não invente dados ausentes. "
            "Para campos não encontrados, utilize null. "
            "O tipo de benefício deve ser um destes valores: "
            "APOSENTADORIA_IDADE, "
            "APOSENTADORIA_TEMPO_CONTRIBUICAO, "
            "APOSENTADORIA_INCAPACIDADE, "
            "AUXILIO_INCAPACIDADE_TEMPORARIA, "
            "AUXILIO_ACIDENTE, "
            "AUXILIO_RECLUSAO, "
            "PENSAO_MORTE, "
            "SALARIO_MATERNIDADE, "
            "BPC_IDOSO, "
            "BPC_DEFICIENCIA, "
            "OUTRO ou NAO_IDENTIFICADO. "
            "A confiança deve variar entre 0 e 1."
            "\n\nConteúdo do documento:\n"
            f"{text}"
        ),
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=GeminiDocumentAnalysis,
        ),
    )

    if isinstance(
        response.parsed,
        GeminiDocumentAnalysis,
    ):
        return response.parsed

    if not response.text:
        raise RuntimeError(
            "O Gemini não retornou uma análise."
        )

    return GeminiDocumentAnalysis.model_validate_json(
        response.text
    )
