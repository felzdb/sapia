from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from .auth import get_current_user, get_db
from .models import Document, User
from .schemas import DocumentResponse
from .storage import get_upload_directory


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


MAX_FILE_SIZE = 20 * 1024 * 1024


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
            detail="O arquivo enviado não parece ser um PDF válido.",
        )

    generated_filename = f"{uuid4()}.pdf"

    upload_directory = get_upload_directory()

    file_path = (
        upload_directory /
        generated_filename
    )

    file_path.write_bytes(content)

    document = Document(
        user_id=current_user.id,
        original_filename=filename,
        stored_filename=generated_filename,
        storage_path=str(file_path),
        size_bytes=len(content),
        status="ENVIADO",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document