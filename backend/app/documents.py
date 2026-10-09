from datetime import datetime
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

    content = generate_petition_text(
        document.benefit_type,
        payload.dados_cliente,
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

    db.commit()
    db.refresh(petition)

    return petition

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

    return petition
