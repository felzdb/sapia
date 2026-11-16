import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import get_current_user, get_db
from app.clauses import PetitionComposition
from app.database import Base
from app.main import app
from app.models import Document, Petition, PetitionAuditLog, User


PETITION_CONTENT = (
    "QUALIFICAÇÃO Maria da Silva, inscrito(a) no CPF sob o nº "
    "529.982.247-25. Conteúdo da petição para teste."
)


class PetitionHistoryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(self.engine, expire_on_commit=False)

        with self.factory() as db:
            self.owner = User(
                name="Usuário proprietário",
                email="owner@example.com",
                password_hash="x",
                role="USUARIO",
                status="ATIVO",
            )
            self.other = User(
                name="Outro usuário",
                email="other@example.com",
                password_hash="x",
                role="USUARIO",
                status="ATIVO",
            )
            self.admin = User(
                name="Administrador",
                email="admin@example.com",
                password_hash="x",
                role="ADMINISTRADOR",
                status="ATIVO",
            )
            db.add_all([self.owner, self.other, self.admin])
            db.flush()

            document = Document(
                user_id=self.owner.id,
                original_filename="documento.pdf",
                stored_filename="documento.pdf",
                storage_path="documento.pdf",
                size_bytes=100,
                status="PROCESSADO",
                benefit_type="APOSENTADORIA_IDADE",
            )
            other_document = Document(
                user_id=self.other.id,
                original_filename="outro.pdf",
                stored_filename="outro.pdf",
                storage_path="outro.pdf",
                size_bytes=100,
                status="PROCESSADO",
                benefit_type="AUXILIO_DOENCA",
            )
            db.add_all([document, other_document])
            db.flush()

            self.petition = Petition(
                document_id=document.id,
                content=PETITION_CONTENT,
                status="GERADA",
                generated_at=datetime(2026, 11, 10, 12, 0, 0),
            )
            self.other_petition = Petition(
                document_id=other_document.id,
                content="QUALIFICAÇÃO João Souza, inscrito(a) no CPF sob o nº 111.444.777-35.",
                status="GERADA",
            )
            db.add_all([self.petition, self.other_petition])
            db.flush()

            self.snapshot = PetitionComposition(
                petition_id=self.petition.id,
                benefit_type="APOSENTADORIA_IDADE",
                case_details={},
                clauses=[],
                warnings=[],
                content=PETITION_CONTENT + " Versão anterior.",
                created_at=datetime(2026, 11, 9, 10, 0, 0),
            )
            db.add(self.snapshot)
            db.commit()
            self.owner_id = self.owner.id
            self.other_id = self.other.id
            self.admin_id = self.admin.id
            self.petition_id = self.petition.id
            self.other_petition_id = self.other_petition.id
            self.snapshot_id = self.snapshot.id

        def test_db():
            with self.factory() as db:
                yield db

        self.current_user = self.owner
        app.dependency_overrides[get_db] = test_db
        app.dependency_overrides[get_current_user] = lambda: self.current_user
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.engine.dispose()

    def set_user(self, user_id):
        with self.factory() as db:
            self.current_user = db.get(User, user_id)

    def test_owner_can_list_own_history_and_filters_work(self):
        response = self.client.get(
            "/documents/history",
            params={
                "client_name": "Maria",
                "cpf": "529.982.247-25",
                "benefit_type": "APOSENTADORIA_IDADE",
                "start_date": "2026-11-01T00:00:00",
                "end_date": "2026-11-30T23:59:59",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()), 1)
        item = response.json()[0]
        self.assertEqual(item["petition_id"], self.petition_id)
        self.assertEqual(item["client_name"], "Maria da Silva")
        self.assertEqual(item["cpf"], "529.982.247-25")
        self.assertEqual(item["benefit_type"], "APOSENTADORIA_IDADE")
        self.assertIsNone(item["owner_name"])

    def test_regular_user_cannot_see_another_users_history_or_detail(self):
        self.set_user(self.other_id)
        response = self.client.get("/documents/history")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["petition_id"] for item in response.json()],
            [self.other_petition_id],
        )
        detail = self.client.get(f"/documents/history/{self.petition_id}")
        self.assertEqual(detail.status_code, 404)

    def test_administrator_can_see_all_history_and_owner_name(self):
        self.set_user(self.admin_id)
        response = self.client.get("/documents/history")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()), 2)
        owner_item = next(
            item for item in response.json()
            if item["petition_id"] == self.petition_id
        )
        self.assertEqual(owner_item["owner_name"], "Usuário proprietário")

    def test_history_versions_are_available_to_owner_and_admin(self):
        response = self.client.get(
            f"/documents/history/{self.petition_id}/versions"
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["version_id"], self.snapshot_id)
        self.assertIn("Versão anterior", response.json()[0]["content"])

        self.set_user(self.admin_id)
        admin_response = self.client.get(
            f"/documents/history/{self.petition_id}/versions"
        )
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(len(admin_response.json()), 1)

    def test_snapshot_can_be_reexported_without_regenerating_petition(self):
        with patch("app.documents.export_petition_pdf", return_value=b"PDF-TESTE"):
            response = self.client.get(
                f"/documents/history/{self.petition_id}/versions/"
                f"{self.snapshot_id}/export/pdf"
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.content, b"PDF-TESTE")
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertIn("_v", response.headers["content-disposition"])

        with patch("app.documents.export_petition_docx", return_value=b"DOCX-TESTE"):
            docx_response = self.client.get(
                f"/documents/history/{self.petition_id}/versions/"
                f"{self.snapshot_id}/export/docx"
            )
        self.assertEqual(docx_response.status_code, 200)
        self.assertEqual(docx_response.content, b"DOCX-TESTE")

        with self.factory() as db:
            petition = db.get(Petition, self.petition_id)
            self.assertEqual(petition.content, PETITION_CONTENT)

    def test_snapshot_from_another_petition_cannot_be_exported(self):
        response = self.client.get(
            f"/documents/history/{self.other_petition_id}/versions/"
            f"{self.snapshot_id}/export/pdf"
        )
        self.assertEqual(response.status_code, 404)

    def test_soft_delete_hides_history_and_creates_audit_log(self):
        response = self.client.delete(
            f"/documents/history/{self.petition_id}"
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            self.client.get("/documents/history").json(),
            [],
        )
        self.assertEqual(
            self.client.get(f"/documents/history/{self.petition_id}").status_code,
            404,
        )
        with self.factory() as db:
            petition = db.get(Petition, self.petition_id)
            audit = db.scalar(
                select(PetitionAuditLog).where(
                    PetitionAuditLog.petition_id == self.petition_id
                )
            )
            self.assertIsNotNone(petition.deleted_at)
            self.assertIsNotNone(audit)
            self.assertEqual(audit.action, "EXCLUSAO")
            self.assertEqual(audit.user_id, self.owner_id)

    def test_regular_user_cannot_delete_another_users_petition(self):
        response = self.client.delete(
            f"/documents/history/{self.other_petition_id}"
        )
        self.assertEqual(response.status_code, 404)
        with self.factory() as db:
            self.assertIsNone(
                db.get(Petition, self.other_petition_id).deleted_at
            )
            self.assertEqual(
                db.scalars(select(PetitionAuditLog)).all(),
                [],
            )


if __name__ == "__main__":
    unittest.main()
