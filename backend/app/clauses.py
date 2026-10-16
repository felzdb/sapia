"""RF8: cadastro versionado, seleção e composição de cláusulas."""
from datetime import datetime
from string import Template
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, Session, mapped_column

from .auth import get_current_user, get_db
from .benefit_identifier import BENEFIT_TYPES
from .database import Base
from .models import User, Petition
from .schemas import ClientDataResponse

CASE_FIELDS = {
    "insalubridade": "Atividade insalubre confirmada",
    "periculosidade": "Atividade perigosa confirmada",
    "gratuidade": "Pedido de justiça gratuita confirmado",
    "tutela_urgencia": "Pedido de tutela de urgência confirmado",
}
SECTIONS = ("fatos", "direito", "pedidos")


class Clause(Base):
    __tablename__ = "clausula"
    id: Mapped[int] = mapped_column(primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    current_version: Mapped[int] = mapped_column(Integer, default=1)


class ClauseVersion(Base):
    __tablename__ = "clausula_versao"
    __table_args__ = (UniqueConstraint("clause_id", "version"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    clause_id: Mapped[int] = mapped_column(ForeignKey("clausula.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    text: Mapped[str] = mapped_column(Text)
    section: Mapped[str] = mapped_column(String(20))
    benefit_types: Mapped[list] = mapped_column(JSON)
    conditions: Mapped[dict] = mapped_column(JSON)
    display_order: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PetitionComposition(Base):
    """Snapshot imutável: preserva texto e regras mesmo após edição/exclusão."""
    __tablename__ = "peticao_composicao"
    id: Mapped[int] = mapped_column(primary_key=True)
    petition_id: Mapped[int] = mapped_column(ForeignKey("peticao.id"), index=True)
    benefit_type: Mapped[str] = mapped_column(String(100))
    case_details: Mapped[dict] = mapped_column(JSON)
    clauses: Mapped[list] = mapped_column(JSON)
    warnings: Mapped[list] = mapped_column(JSON)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ClauseContent(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=255)
    text: str = Field(min_length=1, max_length=30000)
    section: Literal["fatos", "direito", "pedidos"] = "direito"
    benefit_types: list[str] = Field(min_length=1)
    conditions: dict[str, StrictBool] = Field(default_factory=dict)
    display_order: int = Field(default=0, ge=0, le=10000)

    @field_validator("benefit_types")
    @classmethod
    def validate_benefits(cls, value):
        if any(b not in BENEFIT_TYPES or b == "NAO_IDENTIFICADO" for b in value):
            raise ValueError("Tipo de benefício inválido.")
        return sorted(set(value))

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, value):
        if set(value) - CASE_FIELDS.keys():
            raise ValueError("Particularidade desconhecida.")
        return value

    @field_validator("text")
    @classmethod
    def validate_placeholders(cls, value):
        template = Template(value)
        if not template.is_valid():
            raise ValueError("Marcador inválido. Use ${nome}; para cifrão literal, use $$.")
        if set(template.get_identifiers()) - ClientDataResponse.model_fields.keys():
            raise ValueError("Marcador não corresponde a um campo do cliente.")
        return value


class ClauseUpdate(ClauseContent):
    expected_version: int = Field(ge=1)


class CaseDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")
    insalubridade: StrictBool | None = None
    periculosidade: StrictBool | None = None
    gratuidade: StrictBool | None = None
    tutela_urgencia: StrictBool | None = None


router = APIRouter(prefix="/clauses", tags=["Cláusulas RF8"])


def admin(user: User = Depends(get_current_user)):
    if user.role != "ADMINISTRADOR" or user.status != "ATIVO":
        raise HTTPException(403, "Somente o administrador pode gerenciar cláusulas.")
    return user


def serialize(clause, version):
    return {"id": clause.id, "active": clause.active, "version": version.version,
            "title": version.title, "text": version.text, "section": version.section,
            "benefit_types": version.benefit_types, "conditions": version.conditions,
            "display_order": version.display_order, "created_at": version.created_at.isoformat()}


@router.get("/options")
def options(user: User = Depends(get_current_user)):
    return {"benefit_types": [b for b in BENEFIT_TYPES if b != "NAO_IDENTIFICADO"],
            "case_fields": CASE_FIELDS, "sections": SECTIONS,
            "placeholders": list(ClientDataResponse.model_fields)}


@router.get("")
def list_clauses(db: Session = Depends(get_db), user: User = Depends(admin)):
    rows = db.execute(select(Clause, ClauseVersion).join(ClauseVersion,
        (ClauseVersion.clause_id == Clause.id) & (ClauseVersion.version == Clause.current_version))
        .order_by(ClauseVersion.display_order, Clause.id)).all()
    return [serialize(c, v) for c, v in rows]


@router.post("", status_code=201)
def create_clause(payload: ClauseContent, db: Session = Depends(get_db), user: User = Depends(admin)):
    clause = Clause(active=True, current_version=1)
    db.add(clause)
    db.flush()
    version = ClauseVersion(clause_id=clause.id, version=1, created_by=user.id, **payload.model_dump())
    db.add(version)
    db.commit()
    return serialize(clause, version)


@router.put("/{clause_id}")
def edit_clause(clause_id: int, payload: ClauseUpdate, db: Session = Depends(get_db), user: User = Depends(admin)):
    clause = db.get(Clause, clause_id)
    if clause is None or not clause.active:
        raise HTTPException(404, "Cláusula ativa não encontrada.")
    # Atualização condicional impede sobrescrita concorrente de uma versão.
    from sqlalchemy import update
    changed = db.execute(update(Clause).where(Clause.id == clause_id,
        Clause.current_version == payload.expected_version).values(current_version=payload.expected_version + 1))
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "A cláusula foi alterada. Atualize a lista antes de editar.")
    version = ClauseVersion(clause_id=clause_id, version=payload.expected_version + 1,
        created_by=user.id, **payload.model_dump(exclude={"expected_version"}))
    db.add(version)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Conflito de versão. Atualize a lista.")
    return serialize(clause, version)


@router.delete("/{clause_id}", status_code=204)
def delete_clause(clause_id: int, db: Session = Depends(get_db), user: User = Depends(admin)):
    clause = db.get(Clause, clause_id)
    if clause is None:
        raise HTTPException(404, "Cláusula não encontrada.")
    clause.active = False
    db.commit()


@router.get("/{clause_id}/versions")
def versions(clause_id: int, db: Session = Depends(get_db), user: User = Depends(admin)):
    clause = db.get(Clause, clause_id)
    if clause is None:
        raise HTTPException(404, "Cláusula não encontrada.")
    return [serialize(clause, v) for v in db.scalars(select(ClauseVersion)
        .where(ClauseVersion.clause_id == clause_id).order_by(ClauseVersion.version.desc()))]


def select_applicable(db: Session, benefit_type: str, details: dict, client_data: ClientDataResponse):
    """Condições são cumulativas; desconhecido nunca equivale a falso."""
    selected, warnings = [], []
    rows = db.execute(select(Clause, ClauseVersion).join(ClauseVersion,
        (ClauseVersion.clause_id == Clause.id) & (ClauseVersion.version == Clause.current_version))
        .where(Clause.active.is_(True)).order_by(ClauseVersion.display_order, Clause.id)).all()
    values = {k: ", ".join(v) if isinstance(v, list) else v or f"[PREENCHER {k.upper()}]"
              for k, v in client_data.model_dump().items()}
    for clause, version in rows:
        if benefit_type not in version.benefit_types:
            continue
        if any(details.get(k) is not None and details[k] != expected for k, expected in version.conditions.items()):
            continue
        unknown = [CASE_FIELDS[k] for k in version.conditions if details.get(k) is None]
        if unknown:
            warnings.append(f'Cláusula "{version.title}" omitida: confirme {", ".join(unknown)}.')
            continue
        data = serialize(clause, version)
        data["rendered_text"] = Template(version.text).substitute(values)
        selected.append(data)
    if not selected:
        warnings.append("Nenhuma cláusula do banco se aplica aos dados confirmados. Revise o cadastro e o caso.")
    return selected, warnings


def petition_response(db: Session, petition: Petition):
    snapshot = db.scalar(select(PetitionComposition).where(PetitionComposition.petition_id == petition.id)
                         .order_by(PetitionComposition.id.desc()))
    return {"id": petition.id, "document_id": petition.document_id, "content": petition.content,
            "status": petition.status, "generated_at": petition.generated_at,
            "clauses": snapshot.clauses if snapshot else [], "warnings": snapshot.warnings if snapshot else []}
