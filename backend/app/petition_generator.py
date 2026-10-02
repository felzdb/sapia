from .schemas import ClientDataResponse


BENEFIT_NAMES = {
    "APOSENTADORIA_IDADE": "Aposentadoria por Idade",
    "APOSENTADORIA_TEMPO_CONTRIBUICAO": "Aposentadoria por Tempo de Contribuição",
    "APOSENTADORIA_INCAPACIDADE": "Aposentadoria por Incapacidade Permanente",
    "AUXILIO_INCAPACIDADE_TEMPORARIA": "Auxílio por Incapacidade Temporária",
    "AUXILIO_ACIDENTE": "Auxílio-Acidente",
    "AUXILIO_RECLUSAO": "Auxílio-Reclusão",
    "PENSAO_MORTE": "Pensão por Morte",
    "SALARIO_MATERNIDADE": "Salário-Maternidade",
    "BPC_IDOSO": "Benefício de Prestação Continuada ao Idoso",
    "BPC_DEFICIENCIA": "Benefício de Prestação Continuada à Pessoa com Deficiência",
    "OUTRO": "Benefício Previdenciário",
    "NAO_IDENTIFICADO": "Benefício Previdenciário",
}

BENEFIT_SECTIONS = {
    "APOSENTADORIA_IDADE": {
        "titulo": "PETIÇÃO INICIAL - APOSENTADORIA POR IDADE",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Aposentadoria por Idade."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis à Aposentadoria por Idade e os documentos "
            "apresentados no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis à "
            "Aposentadoria por Idade."
        ),
    },
    "APOSENTADORIA_TEMPO_CONTRIBUICAO": {
        "titulo": "PETIÇÃO INICIAL - APOSENTADORIA POR TEMPO DE CONTRIBUIÇÃO",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Aposentadoria por Tempo de Contribuição."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis à Aposentadoria por Tempo de Contribuição e os "
            "documentos apresentados no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis à "
            "Aposentadoria por Tempo de Contribuição."
        ),
    },
    "APOSENTADORIA_INCAPACIDADE": {
        "titulo": "PETIÇÃO INICIAL - APOSENTADORIA POR INCAPACIDADE PERMANENTE",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Aposentadoria por Incapacidade Permanente."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis à Aposentadoria por Incapacidade Permanente e "
            "os documentos apresentados no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis à "
            "Aposentadoria por Incapacidade Permanente."
        ),
    },
    "AUXILIO_INCAPACIDADE_TEMPORARIA": {
        "titulo": "PETIÇÃO INICIAL - AUXÍLIO POR INCAPACIDADE TEMPORÁRIA",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Auxílio por Incapacidade Temporária."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis ao Auxílio por Incapacidade Temporária e os "
            "documentos apresentados no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis ao "
            "Auxílio por Incapacidade Temporária."
        ),
    },
    "AUXILIO_ACIDENTE": {
        "titulo": "PETIÇÃO INICIAL - AUXÍLIO-ACIDENTE",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Auxílio-Acidente."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis ao Auxílio-Acidente e os documentos apresentados "
            "no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis ao "
            "Auxílio-Acidente."
        ),
    },
    "AUXILIO_RECLUSAO": {
        "titulo": "PETIÇÃO INICIAL - AUXÍLIO-RECLUSÃO",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Auxílio-Reclusão."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis ao Auxílio-Reclusão e os documentos apresentados "
            "no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis ao "
            "Auxílio-Reclusão."
        ),
    },
    "PENSAO_MORTE": {
        "titulo": "PETIÇÃO INICIAL - PENSÃO POR MORTE",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Pensão por Morte."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis à Pensão por Morte e os documentos apresentados "
            "no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis à "
            "Pensão por Morte."
        ),
    },
    "SALARIO_MATERNIDADE": {
        "titulo": "PETIÇÃO INICIAL - SALÁRIO-MATERNIDADE",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Salário-Maternidade."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis ao Salário-Maternidade e os documentos "
            "apresentados no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis ao "
            "Salário-Maternidade."
        ),
    },
    "BPC_IDOSO": {
        "titulo": "PETIÇÃO INICIAL - BENEFÍCIO DE PRESTAÇÃO CONTINUADA AO IDOSO",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Benefício de Prestação Continuada ao Idoso."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis ao Benefício de Prestação Continuada ao Idoso e "
            "os documentos apresentados no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis ao "
            "Benefício de Prestação Continuada ao Idoso."
        ),
    },
    "BPC_DEFICIENCIA": {
        "titulo": "PETIÇÃO INICIAL - BENEFÍCIO DE PRESTAÇÃO CONTINUADA À PESSOA COM DEFICIÊNCIA",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a pedido de Benefício de Prestação Continuada à Pessoa "
            "com Deficiência."
        ),
        "direito": (
            "A pretensão deve ser analisada considerando os requisitos "
            "aplicáveis ao Benefício de Prestação Continuada à Pessoa "
            "com Deficiência e os documentos apresentados no caso concreto."
        ),
        "pedido": (
            "A análise do preenchimento dos requisitos aplicáveis ao "
            "Benefício de Prestação Continuada à Pessoa com Deficiência."
        ),
    },
    "OUTRO": {
        "titulo": "PETIÇÃO INICIAL - BENEFÍCIO PREVIDENCIÁRIO",
        "fatos": (
            "O documento analisado foi identificado como relacionado "
            "a benefício previdenciário não enquadrado nos modelos específicos."
        ),
        "direito": (
            "A pretensão deve ser analisada conforme a legislação "
            "previdenciária aplicável e os documentos apresentados "
            "no caso concreto."
        ),
        "pedido": (
            "A análise do direito previdenciário apresentado no caso concreto."
        ),
    },
}

def generate_petition_text(
    benefit_type: str,
    client_data: ClientDataResponse,
) -> str:
    benefit_name = BENEFIT_NAMES.get(
        benefit_type,
        "Benefício Previdenciário",
    )

    benefit_sections = BENEFIT_SECTIONS.get(
        benefit_type,
        BENEFIT_SECTIONS["OUTRO"],
    )

    nome = client_data.nome or "[NOME NÃO IDENTIFICADO]"
    cpf = client_data.cpf or "[CPF NÃO IDENTIFICADO]"
    data_nascimento = (
        client_data.data_nascimento
        or "[DATA DE NASCIMENTO NÃO IDENTIFICADA]"
    )
    nit_pis = client_data.nit_pis or "[NIT/PIS NÃO IDENTIFICADO]"
    numero_beneficio = (
        client_data.numero_beneficio
        or "[NÚMERO DO BENEFÍCIO NÃO IDENTIFICADO]"
    )
    dib = (
        client_data.data_inicio_beneficio
        or "[DIB NÃO IDENTIFICADA]"
    )
    valor = (
        client_data.valor_beneficio
        or "[VALOR NÃO IDENTIFICADO]"
    )

    return f"""AO JUÍZO COMPETENTE

{benefit_sections["titulo"]}

QUALIFICAÇÃO

{nome}, inscrito(a) no CPF sob o nº {cpf}, nascido(a) em
{data_nascimento}, inscrito(a) no NIT/PIS sob o nº {nit_pis},
vem apresentar a presente PETIÇÃO INICIAL referente ao benefício
de {benefit_name}.

DOS FATOS

{benefit_sections["fatos"]}

O requerente possui benefício identificado sob o nº
{numero_beneficio}, com data de início em {dib} e valor informado
de {valor}.

DO DIREITO

{benefit_sections["direito"]}

DOS PEDIDOS

Diante do exposto, requer:

1. O recebimento e processamento da presente petição;
2. {benefit_sections["pedido"].rstrip(".")};
3. A consideração dos documentos e informações apresentados;
4. A adoção das providências cabíveis conforme o caso concreto.

DO VALOR DA CAUSA

Valor a ser definido conforme os elementos do processo.

Termos em que,
Pede deferimento.
"""
