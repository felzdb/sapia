"""RF8 integrada à RF7, sem chamar Gemini nem usar o banco real."""
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from unittest.mock import patch
import app.main as main_module
from app.auth import get_current_user, get_db
from app.database import Base
from app.main import app
from app.models import Document, User
from app.clauses import Clause, ClauseVersion, select_applicable
from app.schemas import ClientDataResponse


class RF8Tests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(self.engine, expire_on_commit=False)
        self.db = self.factory()
        self.admin = User(name="Admin", email="admin@test.com", password_hash="x", role="ADMINISTRADOR", status="ATIVO")
        self.user = User(name="Usuario", email="user@test.com", password_hash="x", role="USUARIO", status="ATIVO")
        self.db.add_all([self.admin, self.user]); self.db.flush()
        self.document = Document(user_id=self.user.id, original_filename="a.pdf", stored_filename="a.pdf",
                                 storage_path="a.pdf", size_bytes=10, benefit_type="APOSENTADORIA_IDADE")
        self.db.add(self.document); self.db.commit()
        self.current = self.admin
        def get_test_db():
            with self.factory() as session:
                yield session
        app.dependency_overrides[get_db] = get_test_db
        app.dependency_overrides[get_current_user] = lambda: self.current
        self.client = TestClient(app)
        self.base = {"title":"Cláusula de teste", "text":"Dados de ${nome}.", "section":"direito",
                     "benefit_types":["APOSENTADORIA_IDADE"], "conditions":{}, "display_order":10}
        self.data = {"nome":"Cliente Teste", "cpf":"529.982.247-25", "data_nascimento":"01/01/1960",
                     "nit_pis":"123", "numero_beneficio":"123", "data_inicio_beneficio":"01/01/2020",
                     "competencias":["01/2020"], "valor_beneficio":"R$ 1.000,00"}

    def tearDown(self):
        app.dependency_overrides.clear(); self.client.close(); self.db.close(); self.engine.dispose()

    def create(self, **changes):
        response = self.client.post("/clauses", json={**self.base, **changes})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_only_admin_can_manage(self):
        clause = self.create()
        self.current = self.user
        for method, path, body in [("GET", "/clauses", None), ("POST", "/clauses", self.base),
            ("PUT", f'/clauses/{clause["id"]}', {**self.base,"expected_version":1}),
            ("DELETE", f'/clauses/{clause["id"]}', None), ("GET", f'/clauses/{clause["id"]}/versions', None)]:
            self.assertEqual(self.client.request(method, path, json=body).status_code, 403)
        self.assertEqual(self.client.get("/clauses/options").status_code, 200)

    def test_validation(self):
        for changes in [{"benefit_types":[]}, {"benefit_types":["INVALIDO"]},
                        {"conditions":{"unknown": True}}, {"conditions":{"gratuidade":"false"}},
                        {"text":"${senha}"}, {"text":"${"}, {"title":"   "}]:
            self.assertEqual(self.client.post("/clauses", json={**self.base, **changes}).status_code, 422)

    def test_conditions_order_and_unknown(self):
        base = self.create(display_order=20)
        yes = self.create(title="Sim", conditions={"insalubridade":True,"periculosidade":False},display_order=1)
        no = self.create(title="Não", conditions={"insalubridade":False},display_order=2)
        self.create(title="Outro benefício", benefit_types=["PENSAO_MORTE"])
        def selected(details):
            with self.factory() as db:
                return select_applicable(db, "APOSENTADORIA_IDADE", details, ClientDataResponse(nome="Teste"))
        c,w = selected({})
        self.assertEqual([x["id"] for x in c], [base["id"]]); self.assertEqual(len(w),2)
        c,w = selected({"insalubridade":True,"periculosidade":False})
        self.assertEqual([x["id"] for x in c], [yes["id"],base["id"]])
        c,w = selected({"insalubridade":False})
        self.assertEqual([x["id"] for x in c], [no["id"],base["id"]])

    def test_integration_snapshots_versions_and_exclusion(self):
        clause = self.create()
        self.current = self.user
        url = f"/documents/{self.document.id}/petition"
        response = self.client.post(url, json={"dados_cliente":self.data})
        self.assertEqual(response.status_code,200,response.text)
        self.assertIn("Dados de Cliente Teste.",response.json()["content"])
        self.assertEqual(response.json()["clauses"][0]["version"],1)
        self.assertEqual(self.client.patch(url+"/finalize").json()["clauses"][0]["version"],1)
        self.current = self.admin
        changed = {**self.base,"text":"Texto novo.","expected_version":1}
        self.assertEqual(self.client.put(f'/clauses/{clause["id"]}',json=changed).status_code,200)
        self.assertEqual(self.client.put(f'/clauses/{clause["id"]}',json=changed).status_code,409)
        history = self.client.get(f'/clauses/{clause["id"]}/versions').json()
        self.assertEqual([v["version"] for v in history],[2,1])
        self.current = self.user
        self.assertEqual(self.client.post(url,json={"dados_cliente":self.data}).json()["clauses"][0]["version"],2)
        snapshots = self.client.get(url+"/versions").json()
        self.assertIn("Dados de Cliente Teste.", snapshots[1]["content"])
        self.current = self.admin
        self.assertEqual(self.client.delete(f'/clauses/{clause["id"]}').status_code,204)
        self.current = self.user
        result = self.client.post(url,json={"dados_cliente":self.data}).json()
        self.assertEqual(result["clauses"],[])
        self.assertTrue(result["warnings"])
        self.assertEqual(len(self.client.get(url+"/versions").json()),3)
        self.current = self.admin
        self.assertEqual(self.client.get(url+"/versions").status_code,404)

    def test_invalid_case_details_rejected(self):
        self.current = self.user
        for details in [{"insalubridade":"false"}, {"desconhecido":True}]:
            response = self.client.post(f"/documents/{self.document.id}/petition",
                json={"dados_cliente":self.data, "case_details":details})
            self.assertEqual(response.status_code,422)

    def test_startup_preserves_clause_bank(self):
        clause = self.create()
        with patch.object(main_module, "engine", self.engine), patch.object(main_module, "SessionLocal", self.factory), patch.object(main_module, "ensure_user_confirmed_at_column", lambda: None):
            for _ in range(2):
                with TestClient(app) as client:
                    self.assertEqual(client.get("/clauses").json()[0]["id"], clause["id"])

    def test_authentication_required(self):
        del app.dependency_overrides[get_current_user]
        self.assertEqual(self.client.get("/clauses/options").status_code, 401)
        self.assertEqual(self.client.post("/clauses",json=self.base).status_code,401)

    def test_section_placement_and_multiple_benefits(self):
        for section in ("fatos", "direito", "pedidos"):
            self.create(title=f"TESTE_{section}", text=f"CONTEUDO_{section}", section=section,
                        benefit_types=["PENSAO_MORTE", "APOSENTADORIA_IDADE"])
        self.current = self.user
        response = self.client.post(f"/documents/{self.document.id}/petition",json={"dados_cliente":self.data})
        self.assertEqual(response.status_code,200,response.text)
        text = response.json()["content"]
        self.assertLess(text.index("DOS FATOS"),text.index("CONTEUDO_fatos"))
        self.assertLess(text.index("CONTEUDO_direito"),text.index("DOS FATOS"))
        self.assertLess(text.index("DO DIREITO"),text.index("CONTEUDO_direito"))
        self.assertLess(text.index("CONTEUDO_fatos"),text.index("DOS PEDIDOS"))
        self.assertLess(text.index("DOS PEDIDOS"),text.index("CONTEUDO_pedidos"))
        self.assertLess(text.index("CONTEUDO_pedidos"),text.index("DO VALOR DA CAUSA"))

    def test_reopening_sessions_keeps_versions(self):
        clause = self.create()
        with self.factory() as db:
            self.assertEqual(db.get(Clause, clause["id"]).current_version,1)
            self.assertEqual(db.scalar(select(ClauseVersion)).text,self.base["text"])


if __name__ == "__main__": unittest.main()
