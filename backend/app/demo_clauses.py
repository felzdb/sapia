"""Exemplos acadêmicos para os onze benefícios, com cadastro inicial automático."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from .clauses import Clause, ClauseContent, ClauseVersion
from .benefit_identifier import BENEFIT_TYPES
from .petition_generator import BENEFIT_NAMES

LEGACY_BENEFITS = {"APOSENTADORIA_IDADE", "AUXILIO_INCAPACIDADE_TEMPORARIA"}
BENEFITS = [benefit for benefit in BENEFIT_TYPES if benefit != "NAO_IDENTIFICADO"]

DEMO_CLAUSES = (
    {
        "title": "[DEMO RF8] Aposentadoria por Idade",
        "text": (
            "EXEMPLO ACADÊMICO. O caso de ${nome}, CPF ${cpf}, foi identificado "
            "como relacionado à Aposentadoria por Idade, com benefício informado "
            "sob o número ${numero_beneficio}. Este trecho demonstra a seleção "
            "pelo tipo de benefício, sem concluir sobre o direito à concessão."
        ),
        "section": "fatos",
        "benefit_types": ["APOSENTADORIA_IDADE"],
        "conditions": {},
        "display_order": 10,
    },
    {
        "title": "[DEMO RF8] Auxílio por Incapacidade Temporária",
        "text": (
            "EXEMPLO ACADÊMICO O caso de ${nome}, CPF ${cpf}, foi identificado "
            "como relacionado ao Auxílio por Incapacidade Temporária, com benefício "
            "informado sob o número ${numero_beneficio}. Este trecho demonstra a "
            "seleção pelo tipo de benefício, sem concluir sobre o direito à concessão."
        ),
        "section": "fatos",
        "benefit_types": ["AUXILIO_INCAPACIDADE_TEMPORARIA"],
        "conditions": {},
        "display_order": 10,
    },
    {
        "title": "[DEMO RF8] Atividade insalubre",
        "text": (
            "EXEMPLO ACADÊMICO. Na conferência do caso de ${nome}, o usuário "
            "confirmou a informação de atividade insalubre. A seleção deste trecho "
            "registra a particularidade informada, sem reconhecer automaticamente "
            "tempo especial ou qualquer direito previdenciário."
        ),
        "section": "fatos",
        "benefit_types": BENEFITS,
        "conditions": {"insalubridade": True},
        "display_order": 20,
    },
    {
        "title": "[DEMO RF8] Atividade perigosa",
        "text": (
            "EXEMPLO ACADÊMICO. Na conferência do caso de ${nome}, o usuário "
            "confirmou a informação de atividade perigosa. A seleção deste trecho "
            "registra a particularidade informada, sem reconhecer automaticamente "
            "tempo especial ou qualquer direito previdenciário."
        ),
        "section": "fatos",
        "benefit_types": BENEFITS,
        "conditions": {"periculosidade": True},
        "display_order": 30,
    },
    {
        "title": "[DEMO RF8] Pedido de justiça gratuita",
        "text": (
            "EXEMPLO ACADÊMICO. Para o caso de ${nome}, foi confirmada a "
            "inclusão de pedido de justiça gratuita. Este texto demonstra a "
            "seleção da cláusula quando a opção correspondente está marcada "
            "como Sim, sem atestar o preenchimento de requisitos legais."
        ),
        "section": "pedidos",
        "benefit_types": BENEFITS,
        "conditions": {"gratuidade": True},
        "display_order": 40,
    },
    {
        "title": "[DEMO RF8] Pedido de tutela de urgência",
        "text": (
            "EXEMPLO ACADÊMICO. Para o caso de ${nome}, foi confirmada a "
            "inclusão de pedido de tutela de urgência. Este texto demonstra a "
            "seleção da cláusula quando a opção correspondente está marcada "
            "como Sim, sem atestar o preenchimento de requisitos legais."
        ),
        "section": "pedidos",
        "benefit_types": BENEFITS,
        "conditions": {"tutela_urgencia": True},
        "display_order": 50,
    },
)


# Mantém os seis exemplos originais e inclui os nove benefícios restantes.
DEMO_CLAUSES = DEMO_CLAUSES + tuple(
    {
        "title": f"[DEMO RF8] {BENEFIT_NAMES[benefit]}",
        "text": (
            "EXEMPLO ACADÊMICO. Caso de ${nome}, CPF ${cpf}. "
            f"Benefício confirmado no caso: {BENEFIT_NAMES[benefit]}. "
            "Número informado: ${numero_beneficio}. Este trecho demonstra "
            "a seleção pelo benefício e não conclui sobre o direito à concessão."
        ),
        "section": "fatos",
        "benefit_types": [benefit],
        "conditions": {},
        "display_order": 10,
    }
    for benefit in BENEFITS
    if benefit not in LEGACY_BENEFITS
)


def _unchanged_legacy_conditional(version, content):
    """Reconhece apenas a versão original dos quatro exemplos condicionais."""
    return (
        bool(content.conditions)
        and version.version == 1
        and set(version.benefit_types) == LEGACY_BENEFITS
        and version.title == content.title
        and version.text == content.text
        and version.section == content.section
        and version.conditions == content.conditions
        and version.display_order == content.display_order
    )


def register_demo_clauses(db: Session, user_id: int) -> dict:
    """Preserva exemplos já cadastrados, editados ou excluídos pelo administrador.

    A versão inicial mantém o título original, permitindo reconhecer os exemplos
    mesmo após edição. Repetir o cadastro não reativa nem sobrescreve cláusulas.
    Os quatro exemplos originais sem edição ganham versão 2, vinculada aos
    onze benefícios. Qualquer exemplo editado ou excluído é preservado.
    """
    created = []
    skipped = []
    updated = []
    for example in DEMO_CLAUSES:
        content = ClauseContent.model_validate(example)
        existing = db.scalar(
            select(ClauseVersion.clause_id)
            .where(ClauseVersion.title == content.title)
            .limit(1)
        )
        if existing is not None:
            clause = db.get(Clause, existing)
            current = db.scalar(select(ClauseVersion).where(
                ClauseVersion.clause_id == existing,
                ClauseVersion.version == clause.current_version,
            ))
            if clause.active and current and _unchanged_legacy_conditional(current, content):
                clause.current_version = 2
                db.add(ClauseVersion(
                    clause_id=clause.id, version=2, created_by=user_id,
                    **content.model_dump(),
                ))
                updated.append(content.title)
            else:
                skipped.append(content.title)
            continue

        clause = Clause(active=True, current_version=1)
        db.add(clause)
        db.flush()
        db.add(ClauseVersion(
            clause_id=clause.id,
            version=1,
            created_by=user_id,
            **content.model_dump(),
        ))
        created.append(content.title)

    db.commit()
    return {"created": len(created), "skipped": len(skipped),
            "updated": len(updated), "total": len(DEMO_CLAUSES), "titles": created}
