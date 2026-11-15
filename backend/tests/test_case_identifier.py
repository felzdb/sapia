import unittest
from app.case_identifier import FIELDS, identify_case_details


class CaseIdentifierTests(unittest.TestCase):
    def test_empty_and_plain_benefit_leave_everything_unknown(self):
        for text in ("", "Aposentadoria por Idade. Renda mensal de R$ 1.000,00. Nome: Maria."):
            result=identify_case_details(text)
            self.assertEqual(set(result),set(FIELDS))
            self.assertTrue(all(s["value"] is None and s["status"]=="not_found" for s in result.values()))

    def test_explicit_four_fields(self):
        text="Atividade insalubre: Sim\nAtividade perigosa: Não\nPedido de justiça gratuita: Sim\nPedido de tutela de urgência: Não"
        result=identify_case_details(text)
        for key,value in {"insalubridade":True,"periculosidade":False,"gratuidade":True,"tutela_urgencia":False}.items():
            with self.subTest(key=key):
                self.assertIs(result[key]["value"],value)
                self.assertEqual(result[key]["status"],"suggested")
                self.assertTrue(result[key]["evidence"])
                for item in result[key]["evidence"]:self.assertIn(item["quote"],text)

    def test_natural_language_explicit_requests_and_activity(self):
        text="O segurado exerceu atividade insalubre.\nRequer a concessão dos benefícios da justiça gratuita.\nNão requer tutela de urgência."
        result=identify_case_details(text)
        self.assertIs(result["insalubridade"]["value"],True)
        self.assertIs(result["gratuidade"]["value"],True)
        self.assertIs(result["tutela_urgencia"]["value"],False)
        self.assertIsNone(result["periculosidade"]["value"])

    def test_negation_does_not_become_positive(self):
        for text in ["Não exerceu atividade insalubre.","Não se requer justiça gratuita.","Não\nexerce atividade perigosa."]:
            result=identify_case_details(text)
            detected=[s for s in result.values() if s["status"]=="suggested"]
            self.assertTrue(detected,text)
            self.assertTrue(all(s["value"] is False for s in detected),text)

    def test_absence_of_evidence_and_hypotheticals_are_not_no(self):
        texts=["Não foi comprovada atividade insalubre.","Não há provas de que\nexerce atividade insalubre.",
            "Se necessário, requer tutela de urgência.","Pode requerer justiça gratuita.",
            "Pedido de justiça gratuita: Não informado", "Atividade perigosa: Não confirmada"]
        for text in texts:
            with self.subTest(text=text):
                self.assertTrue(all(s["value"] is None for s in identify_case_details(text).values()))

    def test_conflicts_are_unknown_and_keep_both_evidence_pages(self):
        result=identify_case_details("Atividade insalubre: Sim\fAtividade insalubre: Não")
        self.assertIsNone(result["insalubridade"]["value"])
        self.assertEqual(result["insalubridade"]["status"],"conflicting")
        self.assertEqual([e["page"] for e in result["insalubridade"]["evidence"]],[1,2])

    def test_instructions_in_test_documents_are_not_case_facts(self):
        text="Dados do caso\nBenefício: Auxílio por Incapacidade Temporária.\nSugestão para testar as particularidades\nAtividade insalubre: Sim\nPedido de justiça gratuita: Sim"
        self.assertTrue(all(s["value"] is None for s in identify_case_details(text).values()))
        text="Na interface, confirme manualmente: atividade insalubre = Sim; justiça gratuita = Sim."
        self.assertTrue(all(s["value"] is None for s in identify_case_details(text).values()))

    def test_standalone_keywords_do_not_suggest_anything(self):
        result=identify_case_details("O texto cita insalubridade, periculosidade, justiça gratuita e tutela de urgência.")
        self.assertTrue(all(s["value"] is None for s in result.values()))

    def test_multiple_line_labels_and_accents(self):
        result=identify_case_details("PERICULOSIDADE:\nSIM\n\nGRATUIDADE DA JUSTIÇA:\nNÃO")
        self.assertIs(result["periculosidade"]["value"],True)
        self.assertIs(result["gratuidade"]["value"],False)


if __name__=="__main__":unittest.main()
