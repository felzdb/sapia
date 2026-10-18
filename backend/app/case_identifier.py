"""Sugestões de particularidades por declarações explícitas no texto do PDF.

Não decide direitos nem deduz pedidos a partir de renda, idade ou diagnóstico.
A ausência de informação e os conflitos permanecem sem resposta confirmada.
"""
import re
import unicodedata

FIELDS = ("insalubridade", "periculosidade", "gratuidade", "tutela_urgencia")


def normalize(text):
    return "".join(c for c in unicodedata.normalize("NFD", text.lower())
                   if unicodedata.category(c) != "Mn")


VERBS = r"(?:exerce|exerceu|exercia|desempenha|desempenhou|trabalha|trabalhou)"
REQUEST = r"(?:requer(?:-se|eu)?|solicita(?:-se|ou)?|pede|pediu|postula)"
REQUEST_PREFIX = r"(?:a\s+concessao\s+(?:d[ae]\s+|dos?\s+)?)?(?:os?\s+)?(?:beneficios?\s+d[ae]\s+)?(?:a\s+)?"
DENIAL = r"\bnao\s+(?:se\s+)?"

# Valores explicitamente declarados. A palavra isolada não basta para uma sugestão.
TOPICS = {
    "insalubridade": r"(?:atividade\s+insalubre|insalubridade)",
    "periculosidade": r"(?:atividade\s+perigosa|periculosidade)",
    "gratuidade": r"(?:pedido\s+de\s+)?(?:justica\s+gratuita|gratuidade\s+da\s+justica)",
    "tutela_urgencia": r"(?:pedido\s+de\s+)?tutela\s+de\s+urgencia",
}
PATTERNS = {}
for field, topic in TOPICS.items():
    PATTERNS[field] = {
        True: [rf"\b{topic}\s*[:=]\s*sim\b"],
        False: [rf"\b{topic}\s*[:=]\s*nao\b(?!\s+(?:informad|identificad|confirmad|consta))"],
    }

for field, adjective in [("insalubridade", "insalubre"), ("periculosidade", "perigosa")]:
    phrase = rf"{VERBS}\s+(?:em\s+)?(?:uma\s+)?atividade\s+{adjective}\b"
    PATTERNS[field][True].append(rf"\b{phrase}")
    PATTERNS[field][False].append(DENIAL + phrase)
    PATTERNS[field][True].append(rf"\batividade\s+(?:comprovada|caracterizada|reconhecida)\s+como\s+{adjective}\b")

PATTERNS["insalubridade"][True].append(r"\bexposicao\s+a\s+agentes\s+nocivos\s*[:=]?\s*(?:comprovada|confirmada|sim)\b")
PATTERNS["insalubridade"][False].append(r"\bnao\s+(?:ha|houve)\s+exposicao\s+a\s+agentes\s+nocivos\b")

for field in ("gratuidade", "tutela_urgencia"):
    topic = TOPICS[field]
    phrase = rf"{REQUEST}\s+{REQUEST_PREFIX}{topic}\b"
    PATTERNS[field][True].extend([rf"\b{phrase}", rf"\bfoi\s+(?:requerida|solicitada)\s+(?:a\s+)?{topic}\b"])
    PATTERNS[field][False].extend([
        DENIAL + phrase,
        rf"\bnao\s+foi\s+(?:requerida|solicitada)\s+(?:a\s+)?{topic}\b",
        rf"\bnao\s+(?:ha|houve)\s+pedido\s+de\s+{topic}\b",
    ])

INSTRUCTION = re.compile(
    r"\b(?:na interface|para testar|para teste|marque|selecione|confirme manualmente|"
    r"respostas? sugeridas?|exemplo de|caso deseje|se necessario|se houver|pode requerer|"
    r"podera requerer|recomenda.se)\b"
)
UNCERTAIN = re.compile(
    r"\b(?:nao (?:foi |esta |ficou )?comprovad|sem comprovacao|nao foi possivel|"
    r"suspeita|possivel (?:exposicao|atividade)|possivelmente|a apurar|nao consta|sem informacao|"
    r"nao foi informad|nao ha informacao|nao confirma|a confirmar|a verificar|"
    r"nao (?:ha|existem) (?:provas|evidencias|elementos|comprovacao))"
)
INSTRUCTION_HEADING = re.compile(r"^(?:sugest(?:ao|oes)|roteiro|instrucoes|como testar|resultados esperados|exemplos de respostas)\b")
FACT_HEADING = re.compile(r"^(?:dados do caso|informacoes do caso|declaracao|relatorio|particularidades do caso|condicoes de trabalho|requerimentos)\s*:?$")


def fragments(page):
    """Junta linhas quebradas, mas isola seções instrutivas de documentos de teste."""
    lines = page.splitlines()
    factual = []
    instruction_section = False
    for line in lines:
        normalized = normalize(line.strip())
        if INSTRUCTION_HEADING.search(normalized):
            instruction_section = True
        elif FACT_HEADING.search(normalized):
            instruction_section = False
        factual.append("" if instruction_section else line)

    # Uma janela curta reconhece campos cujo valor está na linha seguinte.
    # Não cruza linhas vazias nem seções de instruções.
    for i, line in enumerate(factual):
        if not line.strip():
            continue
        previous = normalize(factual[i - 1].strip()) if i else ""
        # Não reinterpreta uma continuação de frase negada/incerta como afirmativa.
        if previous in {"nao", "nao se"} or UNCERTAIN.search(previous):
            continue
        group = [line]
        for next_line in factual[i + 1:i + 3]:
            if not next_line.strip():
                break
            group.append(next_line)
        candidate = "\n".join(group)
        if len(candidate) > 900 or (INSTRUCTION.search(normalize(candidate)) or UNCERTAIN.search(normalize(candidate))):
            continue
        yield candidate


def identify_case_details(text: str) -> dict:
    evidence = {field: {True: [], False: []} for field in FIELDS}
    for page_number, page in enumerate(text.split("\f"), start=1):
        for candidate in fragments(page):
            normalized = normalize(candidate)
            for field in FIELDS:
                negative = [m.span() for pattern in PATTERNS[field][False]
                            for m in re.finditer(pattern, normalized)]
                positive = [m.span() for pattern in PATTERNS[field][True]
                            for m in re.finditer(pattern, normalized)]
                # Uma expressão negada também contém palavras da afirmativa.
                positive = [(a,b) for a,b in positive
                            if not any(a < end and b > start for start,end in negative)]
                for value, matches in [(True, positive), (False, negative)]:
                    if matches:
                        item = {"quote": candidate.strip(), "page": page_number}
                        if item not in evidence[field][value]:
                            evidence[field][value].append(item)

    result = {}
    for field in FIELDS:
        positive, negative = evidence[field][True], evidence[field][False]
        if positive and negative:
            result[field] = {"value": None, "status": "conflicting",
                "reason": "Foram encontradas declarações divergentes. Confira os trechos e informe a resposta.",
                "evidence": [positive[0], negative[0]]}
        elif positive or negative:
            value = bool(positive)
            result[field] = {"value": value, "status": "suggested",
                "reason": "Sugestão baseada em declaração explícita do documento. Confirme antes de gerar.",
                "evidence": (positive or negative)[:2]}
        else:
            result[field] = {"value": None, "status": "not_found",
                "reason": "Não foi encontrada uma declaração explícita para este campo.", "evidence": []}
    return result
