import unittest

from app.benefit_identifier import identify_benefit, normalize_text


class BenefitIdentifierTests(unittest.TestCase):
    def test_normalizes_accents_and_uppercase(self):
        text = normalize_text("Auxílio-doença")

        self.assertEqual(text, "AUXILIO-DOENCA")

    def test_identifies_retirement_by_age(self):
        result = identify_benefit(
            "Benefício concedido: Aposentadoria por Idade."
        )

        self.assertEqual(result.benefit_type, "APOSENTADORIA_IDADE")
        self.assertEqual(result.confidence, 0.95)

    def test_identifies_retirement_by_contribution_time(self):
        result = identify_benefit(
            "Benefício: Aposentadoria por Tempo de Contribuição."
        )

        self.assertEqual(
            result.benefit_type,
            "APOSENTADORIA_TEMPO_CONTRIBUICAO",
        )

    def test_identifies_permanent_disability_retirement(self):
        result = identify_benefit(
            "Benefício: Aposentadoria por Incapacidade Permanente."
        )

        self.assertEqual(
            result.benefit_type,
            "APOSENTADORIA_INCAPACIDADE",
        )

    def test_identifies_old_disability_retirement_name(self):
        result = identify_benefit(
            "Benefício: Aposentadoria por Invalidez."
        )

        self.assertEqual(
            result.benefit_type,
            "APOSENTADORIA_INCAPACIDADE",
        )

    def test_identifies_temporary_disability_benefit(self):
        result = identify_benefit(
            "Benefício: Auxílio por Incapacidade Temporária."
        )

        self.assertEqual(
            result.benefit_type,
            "AUXILIO_INCAPACIDADE_TEMPORARIA",
        )

    def test_identifies_old_sickness_benefit_name(self):
        result = identify_benefit("Benefício: Auxílio-doença.")

        self.assertEqual(
            result.benefit_type,
            "AUXILIO_INCAPACIDADE_TEMPORARIA",
        )

    def test_identifies_accident_benefit(self):
        result = identify_benefit("Benefício: Auxílio-acidente.")

        self.assertEqual(
            result.benefit_type,
            "AUXILIO_ACIDENTE",
        )

    def test_identifies_prison_benefit(self):
        result = identify_benefit(
            "Benefício: Auxílio-Reclusão."
        )

        self.assertEqual(
            result.benefit_type,
            "AUXILIO_RECLUSAO",
        )

    def test_identifies_death_pension(self):
        result = identify_benefit("Benefício: Pensão por Morte.")

        self.assertEqual(
            result.benefit_type,
            "PENSAO_MORTE",
        )

    def test_identifies_maternity_benefit(self):
        result = identify_benefit("Benefício: Salário-maternidade.")

        self.assertEqual(
            result.benefit_type,
            "SALARIO_MATERNIDADE",
        )

    def test_identifies_bpc_elderly(self):
        result = identify_benefit(
            "Benefício Assistencial ao Idoso."
        )

        self.assertEqual(
            result.benefit_type,
            "BPC_IDOSO",
        )

    def test_identifies_bpc_disability(self):
        result = identify_benefit(
            "Benefício Assistencial à Pessoa com Deficiência."
        )

        self.assertEqual(
            result.benefit_type,
            "BPC_DEFICIENCIA",
        )

    def test_returns_not_identified_for_unknown_text(self):
        result = identify_benefit(
            "Documento sem informação sobre o tipo de benefício."
        )

        self.assertEqual(
            result.benefit_type,
            "NAO_IDENTIFICADO",
        )
        self.assertEqual(result.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()