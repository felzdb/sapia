import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user, get_db
from app.clauses import petition_response
from app.database import Base
from app.main import app
from app.models import Document, Petition, User
from app.petition_generator import clause_display_title, generate_petition_text
from app.schemas import ClientDataResponse


class PetitionParticularsTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(self.engine, expire_on_commit=False)
        with self.factory() as db:
            self.user = User(name="Teste",email="teste@example.com",password_hash="x",role="USUARIO",status="ATIVO")
            db.add(self.user);db.flush()
            document = Document(user_id=self.user.id,original_filename="a.pdf",stored_filename="a.pdf",
                storage_path="a.pdf",size_bytes=100,benefit_type="APOSENTADORIA_IDADE")
            db.add(document);db.commit();self.document_id=document.id
        def test_db():
            with self.factory() as db:yield db
        app.dependency_overrides[get_db]=test_db
        app.dependency_overrides[get_current_user]=lambda:self.user
        self.client=TestClient(app)
        self.data={"nome":"Cliente Exemplo", "cpf":"529.982.247-25", "data_nascimento":"01/01/1960",
            "nit_pis":"123.45678.90-0", "numero_beneficio":"123.456.789-7", "data_inicio_beneficio":"01/01/2020",
            "competencias":["01/2020"],"valor_beneficio":"R$ 1.000,00"}

    def tearDown(self):
        self.client.close();app.dependency_overrides.clear();self.engine.dispose()

    def test_four_answers_appear_between_requests_and_cause_value(self):
        content=generate_petition_text("APOSENTADORIA_IDADE",ClientDataResponse(**self.data),[],{
            "insalubridade":True,"periculosidade":False,"gratuidade":True,"tutela_urgencia":None})
        self.assertIn("Atividade insalubre: Sim",content)
        self.assertIn("Atividade perigosa: Não",content)
        self.assertIn("Pedido de justiça gratuita: Sim",content)
        self.assertIn("Pedido de tutela de urgência: Não informado",content)
        self.assertEqual(content.count("PARTICULARIDADES DO CASO"),1)
        self.assertLess(content.index("DOS PEDIDOS"),content.index("PARTICULARIDADES DO CASO"))
        self.assertLess(content.index("PARTICULARIDADES DO CASO"),content.index("DO VALOR DA CAUSA"))

    def test_clause_title_removes_demo_and_version_only_for_display(self):
        examples = {
            "[DEMO RF8] Aposentadoria por Idade": "Aposentadoria por Idade",
            "[Demo] Atividade insalubre (v1)": "Atividade insalubre",
            "[DEMO RF8] [DEMO] Justiça gratuita (V12)": "Justiça gratuita",
            "Pedido (artigo 5)": "Pedido (artigo 5)",
            "Demonstração de atividade": "Demonstração de atividade",
        }
        for original, expected in examples.items():
            with self.subTest(title=original):
                self.assertEqual(clause_display_title(original),expected)

    def test_petition_has_clean_headings_and_keeps_original_metadata(self):
        clause = {"title":"[DEMO RF8] Atividade insalubre (v1)",
                  "section":"fatos", "rendered_text":"Texto da cláusula.", "version":1}
        content = generate_petition_text("APOSENTADORIA_IDADE",ClientDataResponse(**self.data),[clause])
        self.assertIn("\nAtividade insalubre\nTexto da cláusula.",content)
        self.assertNotIn("[DEMO",content)
        self.assertNotIn("(v1)",content)
        self.assertEqual(clause["title"],"[DEMO RF8] Atividade insalubre (v1)")
        self.assertEqual(clause["version"],1)

    def test_missing_answers_are_not_treated_as_no(self):
        content=generate_petition_text("APOSENTADORIA_IDADE",ClientDataResponse(**self.data))
        self.assertEqual(content.count(": Não informado"),4)

    def test_api_and_finalize_return_the_saved_answers(self):
        url=f"/documents/{self.document_id}/petition"
        details={"insalubridade":True,"periculosidade":False,"gratuidade":False,"tutela_urgencia":None}
        result=self.client.post(url,json={"dados_cliente":self.data,"case_details":details})
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()["case_details"],details)
        finalized=self.client.patch(url+"/finalize")
        self.assertEqual(finalized.status_code,200,finalized.text)
        self.assertEqual(finalized.json()["case_details"],details)
        self.assertIn("Atividade insalubre: Sim",finalized.json()["content"])

    def test_regeneration_keeps_the_original_answers_in_history(self):
        url=f"/documents/{self.document_id}/petition"
        for value in (True,False):
            result=self.client.post(url,json={"dados_cliente":self.data,"case_details":{"insalubridade":value}})
            self.assertEqual(result.status_code,200,result.text)
        history=self.client.get(url+"/versions").json()
        self.assertFalse(history[0]["case_details"]["insalubridade"])
        self.assertIn("Atividade insalubre: Não",history[0]["content"])
        self.assertTrue(history[1]["case_details"]["insalubridade"])
        self.assertIn("Atividade insalubre: Sim",history[1]["content"])

    def test_old_petitions_without_snapshot_do_not_invent_answers(self):
        with self.factory() as db:
            petition=Petition(document_id=self.document_id,content="Conteúdo antigo.")
            db.add(petition);db.commit()
            result=petition_response(db,petition)
            self.assertEqual(result["case_details"],{})
            self.assertEqual(result["content"],"Conteúdo antigo.")


if __name__ == "__main__": unittest.main()
