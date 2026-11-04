import re

from fastapi.responses import Response

from .petition_exporter import export_petition_docx, export_petition_pdf


from datetime import datetime
from decimal import Decimal, InvalidOperation
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_current_user, get_db
from .client_data import extract_client_data
from .case_identifier import identify_case_details
from .models import Document, Petition, User
from .pdf_reader import PDFReadError, read_pdf_document
from .schemas import (
    BenefitCorrectionRequest,
    DocumentResponse,
    PetitionGenerationRequest,
    PetitionResponse,
)
from .storage import get_upload_directory
from .benefit_identifier import BENEFIT_TYPES, identify_benefit
from .gemini_service import analyze_document_text
from .petition_generator import generate_petition_text
from .clauses import CaseDetails, PetitionComposition, select_applicable, petition_response
from pydantic import ValidationError


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


MAX_FILE_SIZE = 20 * 1024 * 1024

def is_valid_cpf(value: str) -> bool:
    cpf = "".join(char for char in value if char.isdigit())

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calculate_digit(length: int) -> int:
        total = sum(
            int(cpf[i]) * (length + 1 - i)
            for i in range(length)
        )

        remainder = (total * 10) % 11
        return 0 if remainder == 10 else remainder

    return (
        calculate_digit(9) == int(cpf[9])
        and calculate_digit(10) == int(cpf[10])
    )

def is_valid_name(value: str) -> bool:
    name = value.strip()
    allowed_separators = {" ", "-", "'", "’"}

    if not name or not all(
        char.isalpha() or char in allowed_separators
        for char in name
    ):
        return False

    letters = [
        char.casefold()
        for char in name
        if char.isalpha()
    ]

    if not letters:
        return False

    if len(letters) >= 3 and len(set(letters)) == 1:
        return False

    return True

def is_valid_date(value: str) -> bool:
    date_text = value.strip()

    try:
        datetime.strptime(date_text, "%d/%m/%Y")
    except ValueError:
        return False

    return True

def is_future_date(value: str) -> bool:
    try:
        parsed_date = datetime.strptime(value.strip(), "%d/%m/%Y").date()
    except ValueError:
        return False

    return parsed_date > datetime.now().date()


def is_date_before(value: str, reference_value: str) -> bool:
    try:
        date = datetime.strptime(value.strip(), "%d/%m/%Y").date()
        reference_date = datetime.strptime(
            reference_value.strip(),
            "%d/%m/%Y",
        ).date()
    except ValueError:
        return False

    return date < reference_date

def is_valid_competencia(value: str) -> bool:
    competencia = value.strip()

    try:
        datetime.strptime(competencia, "%m/%Y")
    except ValueError:
        return False

    return True

def is_valid_benefit_value(value: str) -> bool:
    amount = value.strip()

    cleaned = (
        amount.replace("R$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    try:
        parsed_value = Decimal(cleaned)
    except InvalidOperation:
        return False

    return parsed_value.is_finite() and parsed_value > 0

def is_valid_nit_pis(value: str) -> bool:
    identifier = value.strip()
    allowed_separators = {" ", ".", "-"}

    if not identifier or not all(
        char.isdigit() or char in allowed_separators
        for char in identifier
    ):
        return False

    digits = "".join(char for char in identifier if char.isdigit())

    if len(digits) != 11 or digits == digits[0] * 11:
        return False

    weights = (3, 2, 9, 8, 7, 6, 5, 4, 3, 2)

    total = sum(
        int(digits[index]) * weights[index]
        for index in range(10)
    )

    remainder = total % 11
    check_digit = 11 - remainder

    if check_digit in (10, 11):
        check_digit = 0

    return check_digit == int(digits[10])


def is_valid_benefit_number(value: str) -> bool:
    identifier = value.strip()
    allowed_separators = {" ", ".", "-"}

    if not identifier or not all(
        char.isdigit() or char in allowed_separators
        for char in identifier
    ):
        return False

    digits = "".join(char for char in identifier if char.isdigit())

    if len(digits) != 10 or digits == digits[0] * 10:
        return False

    weights = (2, 9, 8, 7, 6, 5, 4, 3, 2)

    total = sum(
        int(digits[index]) * weights[index]
        for index in range(9)
    )

    remainder = total % 11

    if remainder in (0, 1):
        check_digit = 0
    else:
        check_digit = 11 - remainder

    return check_digit == int(digits[9])

@router.post(
    "/upload",
    response_model=DocumentResponse,
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename = file.filename or ""

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Apenas arquivos PDF são permitidos.",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O arquivo deve possuir no máximo 20 MB.",
        )

    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível processar o documento. Verifique o arquivo e tente novamente.",
        )

    generated_filename = f"{uuid4()}.pdf"

    upload_directory = get_upload_directory()

    file_path = upload_directory / generated_filename
    file_path.write_bytes(content)

    try:
        reading = read_pdf_document(file_path)
    except PDFReadError as exc:
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    try:
        ai_analysis = analyze_document_text(reading.text)

        if ai_analysis.benefit_type not in BENEFIT_TYPES:
            raise ValueError(
                "Tipo de benefício retornado pela IA é inválido."
            )

        benefit_type = ai_analysis.benefit_type
        benefit_confidence = ai_analysis.benefit_confidence
        client_data = ai_analysis.dados_cliente.model_dump()

    except Exception:
        fallback_benefit = identify_benefit(
            reading.text
        )

        benefit_type = fallback_benefit.benefit_type
        benefit_confidence = fallback_benefit.confidence
        client_data = extract_client_data(
            reading.text
        )

    document = Document(
        user_id=current_user.id,
        original_filename=filename,
        stored_filename=generated_filename,
        storage_path=str(file_path),
        size_bytes=len(content),
        status="PROCESSADO",
        extracted_text=reading.text,
        page_count=reading.page_count,
        benefit_type=benefit_type,
        benefit_confidence=benefit_confidence,
        benefit_original_type=benefit_type,
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    return {
        "id": document.id,
        "original_filename": document.original_filename,
        "size_bytes": document.size_bytes,
        "status": document.status,
        "uploaded_at": document.uploaded_at,
        "extracted_text": document.extracted_text,
        "page_count": document.page_count,
        "pages_without_text": list(reading.pages_without_text),
        "benefit_type": document.benefit_type,
        "benefit_confidence": document.benefit_confidence,
        "dados_cliente": client_data,
        "case_suggestions": identify_case_details(reading.text),
    }

@router.patch("/{document_id}/benefit")
def correct_document_benefit(
    document_id: int,
    correction: BenefitCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if correction.benefit_type not in BENEFIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de benefício inválido.",
        )

    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado.",
        )

    document.benefit_type = correction.benefit_type
    document.benefit_corrected_manually = True

    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "benefit_original_type": document.benefit_original_type,
        "benefit_type": document.benefit_type,
        "benefit_confidence": document.benefit_confidence,
        "benefit_corrected_manually": document.benefit_corrected_manually,
    }

@router.post(
    "/{document_id}/petition",
    response_model=PetitionResponse,
)
def generate_document_petition(
    document_id: int,
    payload: PetitionGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado.",
        )

    if (
        not document.benefit_type
        or document.benefit_type == "NAO_IDENTIFICADO"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Confirme o tipo de benefício antes "
                "de gerar a petição."
            ),
        )

    dados = payload.dados_cliente

    if (
        not dados.nome
        or not dados.cpf
        or not dados.data_nascimento
        or not dados.nit_pis
        or not dados.numero_beneficio
        or not dados.data_inicio_beneficio
        or not dados.competencias
        or not dados.valor_beneficio
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Preencha todos os dados obrigatórios antes de gerar a petição.",
        )

    cpf = payload.dados_cliente.cpf

    if not cpf or not is_valid_cpf(cpf):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CPF inválido. Verifique os dígitos informados.",
        )

    if not is_valid_name(dados.nome):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome inválido. Use apenas letras, espaços, hífen ou apóstrofo e não informe apenas a mesma letra repetida.",
        )

    if not is_valid_date(dados.data_nascimento):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data de nascimento inválida. Verifique a data informada.",
        )

    if not is_valid_date(dados.data_inicio_beneficio):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Data de início do benefício inválida. Verifique a data informada.",
        )

    if is_future_date(dados.data_nascimento):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Data de nascimento inválida. "
                "A data de nascimento não pode estar no futuro."
            ),
        )

    if is_date_before(
        dados.data_inicio_beneficio,
        dados.data_nascimento,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Data de início do benefício inválida. "
                "A DIB não pode ser anterior à data de nascimento."
            ),
        )

    if not all(is_valid_competencia(item) for item in dados.competencias):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Competência inválida. Use mês e ano válidos.",
        )

    if not is_valid_benefit_value(dados.valor_beneficio):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valor do benefício inválido. Informe um valor maior que zero.",
        )

    if not is_valid_nit_pis(dados.nit_pis):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "NIT/PIS inválido. Confira os 11 dígitos e o dígito verificador. "
                "Pontos e hífen são opcionais."
            ),
        )

    if not is_valid_benefit_number(dados.numero_beneficio):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Número do benefício inválido. Confira os 10 dígitos e o dígito verificador. "
                "Pontos e hífen são opcionais."
            ),
        )

    try:
        details = CaseDetails.model_validate(payload.case_details).model_dump()
    except ValidationError as exc:
        raise HTTPException(422, "Particularidades do caso inválidas.") from exc
    clauses, warnings = select_applicable(db, document.benefit_type, details, payload.dados_cliente)
    content = generate_petition_text(
        document.benefit_type,
        payload.dados_cliente,
        clauses,
        details,
    )

    petition = db.scalar(
        select(Petition).where(
            Petition.document_id == document.id
        )
    )

    if petition is None:
        petition = Petition(
            document_id=document.id,
            content=content,
            status="GERADA",
        )
        db.add(petition)
    else:
        petition.content = content
        petition.status = "GERADA"
        petition.generated_at = datetime.utcnow()

    db.flush()
    db.add(PetitionComposition(petition_id=petition.id, benefit_type=document.benefit_type,
        case_details=details, clauses=clauses, warnings=warnings, content=content))
    db.commit()
    db.refresh(petition)

    return petition_response(db, petition)

@router.patch(
    "/{document_id}/petition/finalize",
    response_model=PetitionResponse,
)
def finalize_document_petition(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento não encontrado.",
        )

    petition = db.scalar(
        select(Petition).where(
            Petition.document_id == document.id
        )
    )

    if petition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Petição não encontrada.",
        )

    petition.status = "FINALIZADA"

    db.commit()
    db.refresh(petition)

    return petition_response(db, petition)


@router.get("/{document_id}/petition/versions")
def petition_versions(document_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    document = db.scalar(select(Document).where(Document.id == document_id,
                                                Document.user_id == current_user.id))
    if document is None:
        raise HTTPException(404, "Documento não encontrado.")
    petition = db.scalar(select(Petition).where(Petition.document_id == document_id))
    if petition is None:
        raise HTTPException(404, "Petição não encontrada.")
    rows = db.scalars(select(PetitionComposition).where(PetitionComposition.petition_id == petition.id)
                      .order_by(PetitionComposition.id.desc())).all()
    return [{"id": row.id, "created_at": row.created_at, "benefit_type": row.benefit_type,
             "case_details": row.case_details, "clauses": row.clauses,
             "warnings": row.warnings, "content": row.content} for row in rows]


@router.get("/{document_id}/case-suggestions")
def document_case_suggestions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = db.scalar(select(Document).where(
        Document.id == document_id, Document.user_id == current_user.id,
    ))
    if document is None:
        raise HTTPException(404, "Documento não encontrado.")
    return identify_case_details(document.extracted_text or "")


@router.get("/{document_id}/petition/export/{file_format}")
def export_document_petition(
    document_id: int,
    file_format: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exporta a petição existente em Word ou PDF."""

    if file_format not in ("pdf", "docx"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Utilize pdf ou docx.",
        )

    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Documento não encontrado.",
        )

    petition = db.scalar(
        select(Petition).where(
            Petition.document_id == document.id,
        )
    )

    if petition is None:
        raise HTTPException(
            status_code=404,
            detail="Petição não encontrada.",
        )

    # Extrai o CPF do conteúdo da petição.
    cpf_match = re.search(
        r"CPF sob o n[º°o]?\s*([\d.\-]+)",
        petition.content,
        flags=re.IGNORECASE,
    )

    if cpf_match is None:
        raise HTTPException(
            status_code=422,
            detail="Não foi possível identificar o CPF da petição.",
        )

    cpf = re.sub(r"\D", "", cpf_match.group(1))

    if len(cpf) != 11:
        raise HTTPException(
            status_code=422,
            detail="CPF da petição inválido para exportação.",
        )

    export_date = datetime.now().strftime("%Y%m%d")
    sequence = f"{petition.id:04d}"

    filename = f"{cpf}_{export_date}_{sequence}.{file_format}"

    if file_format == "docx":
        content = export_petition_docx(petition.content)
        media_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        )
    else:
        content = export_petition_pdf(petition.content)
        media_type = "application/pdf"

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
