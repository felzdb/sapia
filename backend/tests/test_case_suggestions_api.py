import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user, get_db
from app.database import Base
from app.demo_clauses import register_demo_clauses
from app.main import app
from app.models import User


class CaseSuggestionAPITests(unittest.TestCase):
    def setUp(self):
        self.engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.factory=sessionmaker(self.engine,expire_on_commit=False)
        with self.factory() as db:
            self.user=User(name="Usuario",email="usuario@example.com",password_hash="x",role="USUARIO",status="ATIVO")
            self.other=User(name="Outro",email="outro@example.com",password_hash="x",role="USUARIO",status="ATIVO")
            self.admin=User(name="Admin",email="admin@example.com",password_hash="x",role="ADMINISTRADOR",status="ATIVO")
            db.add_all([self.user,self.other,self.admin]);db.commit()
            register_demo_clauses(db,self.admin.id)
        self.current=self.user
        def test_db():
            with self.factory() as db:yield db
        app.dependency_overrides[get_db]=test_db
        app.dependency_overrides[get_current_user]=lambda:self.current
        self.client=TestClient(app)
        self.temp=tempfile.TemporaryDirectory()
        self.storage=patch("app.documents.get_upload_directory",return_value=Path(self.temp.name))
        self.ai=patch("app.documents.analyze_document_text",side_effect=RuntimeError("IA indisponível no teste"))
        self.storage.start();self.ai.start()

    def tearDown(self):
        self.ai.stop();self.storage.stop();self.client.close()
        app.dependency_overrides.clear();self.engine.dispose();self.temp.cleanup()

    def pdf(self,extra):
        text=("Nome do beneficiário: Cliente Exemplo\nCPF: 529.982.247-25\n"
            "Data de nascimento: 22/7/1987\nNIT/PIS: 321.98765.43-2\n"
            "Número do benefício: 987.654.321-0\n"
            "Tipo de benefício: Auxílio por Incapacidade Temporária\n"
            "Data de início do benefício: 01/7/2026\nCompetências: 07/2026\n"
            "Valor do benefício: R$ 1.875,40\n"+extra)
        with fitz.open() as document:
            document.new_page().insert_text((50,50),text,fontsize=11)
            return document.tobytes()

    def upload(self,extra):
        response=self.client.post("/documents/upload",files={"file":("caso.pdf",self.pdf(extra),"application/pdf")})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def test_upload_returns_suggestions_with_source_and_works_without_ai(self):
        result=self.upload("Atividade insalubre: Sim\nAtividade perigosa: Não\nPedido de justiça gratuita: Sim\nPedido de tutela de urgência: Não informado")
        suggestions=result["case_suggestions"]
        self.assertIs(suggestions["insalubridade"]["value"],True)
        self.assertIs(suggestions["periculosidade"]["value"],False)
        self.assertIs(suggestions["gratuidade"]["value"],True)
        self.assertIsNone(suggestions["tutela_urgencia"]["value"])
        for suggestion in suggestions.values():
            for item in suggestion["evidence"]:
                self.assertIn(item["quote"],result["extracted_text"])
                self.assertEqual(item["page"],1)
        stored=self.client.get(f'/documents/{result["id"]}/case-suggestions')
        self.assertEqual(stored.json(),suggestions)

    def test_suggestions_do_not_override_human_choices_during_generation(self):
        result=self.upload("Atividade insalubre: Sim\nPedido de justiça gratuita: Sim")
        self.assertTrue(result["case_suggestions"]["insalubridade"]["value"])
        details={"insalubridade":False,"periculosidade":False,"gratuidade":True,"tutela_urgencia":None}
        response=self.client.post(f'/documents/{result["id"]}/petition',json={"dados_cliente":result["dados_cliente"],"case_details":details})
        self.assertEqual(response.status_code,200,response.text)
        petition=response.json()
        self.assertEqual(petition["case_details"],details)
        self.assertEqual(len(petition["clauses"]),2)
        self.assertTrue(all(not c["conditions"].get("insalubridade") for c in petition["clauses"]))
        self.assertIn("Atividade insalubre: Não",petition["content"])

    def test_reanalysis_is_restricted_to_document_owner(self):
        result=self.upload("Atividade insalubre: Sim")
        self.current=self.other
        self.assertEqual(self.client.get(f'/documents/{result["id"]}/case-suggestions').status_code,404)
        del app.dependency_overrides[get_current_user]
        self.assertEqual(self.client.get(f'/documents/{result["id"]}/case-suggestions').status_code,401)

    def test_benefit_document_without_case_facts_keeps_unknown_values(self):
        result=self.upload("")
        self.assertTrue(all(s["value"] is None for s in result["case_suggestions"].values()))


if __name__=="__main__":unittest.main()
