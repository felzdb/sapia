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


def generate_petition_text(
    benefit_type: str,
    client_data: ClientDataResponse,
) -> str:
    benefit_name = BENEFIT_NAMES.get(
        benefit_type,
        "Benefício Previdenciário",
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

QUALIFICAÇÃO

{nome}, inscrito(a) no CPF sob o nº {cpf}, nascido(a) em
{data_nascimento}, inscrito(a) no NIT/PIS sob o nº {nit_pis},
vem apresentar a presente PETIÇÃO INICIAL referente ao benefício
de {benefit_name}.

DOS FATOS

O requerente possui benefício identificado sob o nº
{numero_beneficio}, com data de início em {dib} e valor informado
de {valor}.

DO DIREITO

A pretensão refere-se ao benefício de {benefit_name}, devendo o
caso ser analisado conforme a legislação previdenciária aplicável
e os documentos apresentados.

DOS PEDIDOS

Diante do exposto, requer:

1. O recebimento e processamento da presente petição;
2. A análise do direito ao benefício de {benefit_name};
3. A consideração dos documentos e informações apresentados;
4. A adoção das providências cabíveis conforme o caso concreto.

DO VALOR DA CAUSA

Valor a ser definido conforme os elementos do processo.

Termos em que,
Pede deferimento.
"""
