"""Demonstra cadastro e inclusão/omissão reais da RF8 em banco isolado."""
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user, get_db
from app.clauses import Clause, ClauseVersion, PetitionComposition
from app.database import Base
from app.demo_clauses import BENEFITS, DEMO_CLAUSES, LEGACY_BENEFITS
from app.clauses import ClauseContent
from unittest.mock import patch
import app.main as main_module
from app.main import app
from app.models import Document, User
from app.petition_generator import clause_display_title


class DemoClauseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(self.engine, expire_on_commit=False)
        with self.factory() as db:
            self.admin = User(name="Admin", email="admin@example.com", password_hash="x", role="ADMINISTRADOR", status="ATIVO")
            self.user = User(name="Usuario", email="usuario@example.com", password_hash="x", role="USUARIO", status="ATIVO")
            db.add_all([self.admin, self.user])
            db.flush()
            document = Document(user_id=self.user.id, original_filename="demo.pdf", stored_filename="demo.pdf",
                storage_path="demo.pdf", size_bytes=100, benefit_type="APOSENTADORIA_IDADE")
            db.add(document)
            db.commit()
            self.document_id = document.id
        self.current = self.admin
        def test_db():
            with self.factory() as db:
                yield db
        app.dependency_overrides[get_db] = test_db
        app.dependency_overrides[get_current_user] = lambda: self.current
        self.client = TestClient(app)
        self.data = {"nome":"Cliente Exemplo", "cpf":"529.982.247-25", "data_nascimento":"01/01/1960",
            "nit_pis":"123.45678.90-0", "numero_beneficio":"123.456.789-7", "data_inicio_beneficio":"01/01/2020",
            "competencias":["01/2020"], "valor_beneficio":"R$ 1.000,00"}

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def seed(self):
        self.current = self.admin
        response = self.client.post("/clauses/demo-examples")
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def petition(self, benefit, details):
        self.current = self.user
        result = self.client.patch(f"/documents/{self.document_id}/benefit",json={"benefit_type":benefit})
        self.assertEqual(result.status_code,200,result.text)
        response = self.client.post(f"/documents/{self.document_id}/petition",json={"dados_cliente":self.data,"case_details":details})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def test_registers_fifteen_once(self):
        self.assertEqual(self.seed()["created"],15)
        result = self.seed()
        self.assertEqual((result["created"],result["skipped"]),(0,15))
        with self.factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(Clause)),15)
            self.assertEqual(db.scalar(select(func.count()).select_from(ClauseVersion)),15)

    def test_admin_and_authentication_required(self):
        self.current = self.user
        self.assertEqual(self.client.post("/clauses/demo-examples").status_code,403)
        self.current = self.admin
        self.current.status = "PENDENTE"
        self.assertEqual(self.client.post("/clauses/demo-examples").status_code,403)
        del app.dependency_overrides[get_current_user]
        self.assertEqual(self.client.post("/clauses/demo-examples").status_code,401)

    def test_selection_matrix_and_rendered_petition(self):
        self.seed()
        age = DEMO_CLAUSES[0]["title"]
        incapacity = DEMO_CLAUSES[1]["title"]
        insal = DEMO_CLAUSES[2]["title"]
        danger = DEMO_CLAUSES[3]["title"]
        gratuity = DEMO_CLAUSES[4]["title"]
        urgency = DEMO_CLAUSES[5]["title"]
        scenarios = [
            ("idade com duas condições", "APOSENTADORIA_IDADE",
             {"insalubridade":True,"periculosidade":False,"gratuidade":True,"tutela_urgencia":False}, [age,insal,gratuity], 0),
            ("idade com todas não", "APOSENTADORIA_IDADE",
             {"insalubridade":False,"periculosidade":False,"gratuidade":False,"tutela_urgencia":False}, [age], 0),
            ("idade sem confirmação", "APOSENTADORIA_IDADE", {}, [age], 4),
            ("incapacidade com duas condições", "AUXILIO_INCAPACIDADE_TEMPORARIA",
             {"insalubridade":True,"periculosidade":False,"gratuidade":True,"tutela_urgencia":False}, [incapacity,insal,gratuity], 0),
            ("todas sim", "APOSENTADORIA_IDADE",
             {"insalubridade":True,"periculosidade":True,"gratuidade":True,"tutela_urgencia":True}, [age,insal,danger,gratuity,urgency], 0),
            ("pensão por morte", "PENSAO_MORTE",
             {"insalubridade":False,"periculosidade":False,"gratuidade":False,"tutela_urgencia":False},
             [next(c["title"] for c in DEMO_CLAUSES if c["benefit_types"] == ["PENSAO_MORTE"])], 0),
        ]
        for label, benefit, details, expected, warning_count in scenarios:
            with self.subTest(label=label):
                result = self.petition(benefit,details)
                self.assertEqual([c["title"] for c in result["clauses"]],expected)
                self.assertEqual(len(result["warnings"]),warning_count)
                for item in DEMO_CLAUSES:
                    self.assertEqual(f'\n{clause_display_title(item["title"])}\n' in result["content"],item["title"] in expected)
                for clause in result["clauses"]:
                    self.assertIn("Cliente Exemplo",clause["rendered_text"])
                    self.assertNotIn("${nome}",clause["rendered_text"])
        self.current = self.user
        history = self.client.get(f"/documents/{self.document_id}/petition/versions").json()
        self.assertEqual(len(history),6)
        self.assertEqual(len(history[-1]["clauses"]),3)
        self.assertIn(f"\n{clause_display_title(insal)}\n", history[-1]["content"])

    def test_reregister_does_not_overwrite_edited_or_reactivate_deleted(self):
        self.seed()
        clauses = self.client.get("/clauses").json()
        first = clauses[0]
        payload = {key:first[key] for key in ["title","text","section","benefit_types","conditions","display_order"]}
        payload.update(title="Título editado pelo administrador",text="Texto personalizado.",expected_version=1)
        response = self.client.put(f'/clauses/{first["id"]}',json=payload)
        self.assertEqual(response.status_code,200,response.text)
        second = clauses[1]
        self.assertEqual(self.client.delete(f'/clauses/{second["id"]}').status_code,204)
        result = self.seed()
        self.assertEqual((result["created"],result["skipped"]),(0,15))
        current = {c["id"]:c for c in self.client.get("/clauses").json()}
        self.assertEqual(current[first["id"]]["text"],"Texto personalizado.")
        self.assertEqual(current[first["id"]]["version"],2)
        self.assertFalse(current[second["id"]]["active"])

    def test_all_eleven_benefits_get_one_base_and_matching_conditionals(self):
        self.seed()
        self.assertEqual(len(BENEFITS),11)
        for benefit in BENEFITS:
            with self.subTest(benefit=benefit):
                result = self.petition(benefit, {
                    "insalubridade":True, "periculosidade":False,
                    "gratuidade":True, "tutela_urgencia":False,
                })
                self.assertEqual(len(result["clauses"]),3)
                bases = [c for c in result["clauses"] if not c["conditions"]]
                self.assertEqual(len(bases),1)
                self.assertEqual(bases[0]["benefit_types"],[benefit])
                self.assertEqual(result["warnings"],[])

    def test_automatic_startup_is_repeatable_and_preserves_deleted_examples(self):
        with patch.object(main_module,"engine",self.engine), patch.object(main_module,"SessionLocal",self.factory), patch.object(main_module,"ensure_user_confirmed_at_column",lambda: None):
            with TestClient(app) as client:
                clauses = client.get("/clauses").json()
                self.assertEqual(len(clauses),15)
                deleted_id = clauses[0]["id"]
                self.assertEqual(client.delete(f"/clauses/{deleted_id}").status_code,204)
            with TestClient(app) as client:
                clauses = client.get("/clauses").json()
                self.assertEqual(len(clauses),15)
                self.assertFalse(next(c for c in clauses if c["id"] == deleted_id)["active"])

    def test_upgrade_unedited_legacy_example_creates_version_two(self):
        original = dict(DEMO_CLAUSES[2])
        original["benefit_types"] = sorted(LEGACY_BENEFITS)
        response = self.client.post("/clauses",json=original)
        self.assertEqual(response.status_code,201,response.text)
        clause_id = response.json()["id"]
        result = self.seed()
        self.assertEqual(result["created"],14)
        self.assertEqual(result["updated"],1)
        history = self.client.get(f"/clauses/{clause_id}/versions").json()
        self.assertEqual([v["version"] for v in history],[2,1])
        self.assertEqual(set(history[0]["benefit_types"]),set(BENEFITS))
        self.assertEqual(set(history[1]["benefit_types"]),LEGACY_BENEFITS)
        self.assertEqual(self.seed()["updated"],0)

    def test_examples_persist_after_reopening_database(self):
        self.seed()
        with self.factory() as db:
            self.assertEqual(db.scalar(select(func.count()).select_from(ClauseVersion)),15)
            self.assertTrue(all(c.active for c in db.scalars(select(Clause))))


if __name__ == "__main__":
    unittest.main()
