import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import Base, Document
from app.schema_updates import ensure_document_benefit_columns


class SchemaUpdateTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")

    def tearDown(self):
        self.engine.dispose()

    def create_legacy_table(self):
        with self.engine.begin() as c:
            c.exec_driver_sql('''CREATE TABLE documento (
                id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                stored_filename VARCHAR(255) NOT NULL,
                storage_path VARCHAR(500) NOT NULL,
                size_bytes INTEGER NOT NULL, status VARCHAR(30) NOT NULL,
                extracted_text TEXT, page_count INTEGER, uploaded_at DATETIME NOT NULL
            )''')
            c.exec_driver_sql('''INSERT INTO documento (
                id, user_id, original_filename, stored_filename, storage_path,
                size_bytes, status, extracted_text, page_count, uploaded_at
            ) VALUES (1,1,'antigo.pdf','antigo.pdf','uploads/antigo.pdf',100,
                      'PROCESSADO','Texto antigo',1,'2026-01-01 00:00:00')''')

    def test_migrates_legacy_table_and_allows_orm_insert(self):
        self.create_legacy_table()
        ensure_document_benefit_columns(self.engine)
        with Session(self.engine) as db:
            old = db.get(Document, 1)
            self.assertEqual(old.original_filename, "antigo.pdf")
            self.assertEqual(old.extracted_text, "Texto antigo")
            self.assertIsNone(old.benefit_type)
            self.assertFalse(old.benefit_corrected_manually)
            document = Document(user_id=1, original_filename="novo.pdf", stored_filename="novo.pdf",
                storage_path="uploads/novo.pdf", size_bytes=100, status="PROCESSADO",
                extracted_text="Novo texto", page_count=1, benefit_type="APOSENTADORIA_IDADE",
                benefit_confidence=0.95, benefit_original_type="APOSENTADORIA_IDADE")
            db.add(document)
            db.commit()
            self.assertEqual(db.get(Document, document.id).benefit_type, "APOSENTADORIA_IDADE")

    def test_repeated_update_preserves_schema_and_rows(self):
        self.create_legacy_table()
        ensure_document_benefit_columns(self.engine)
        with self.engine.begin() as c:
            before = c.exec_driver_sql("PRAGMA table_info(documento)").fetchall()
        ensure_document_benefit_columns(self.engine)
        with self.engine.begin() as c:
            self.assertEqual(c.exec_driver_sql("PRAGMA table_info(documento)").fetchall(), before)
            self.assertEqual(c.exec_driver_sql("SELECT count(*) FROM documento").scalar(), 1)

    def test_partial_update_preserves_existing_benefit_and_other_tables(self):
        self.create_legacy_table()
        with self.engine.begin() as c:
            c.exec_driver_sql("ALTER TABLE documento ADD COLUMN benefit_type VARCHAR(100)")
            c.exec_driver_sql("UPDATE documento SET benefit_type='PENSAO_MORTE'")
            c.exec_driver_sql("CREATE TABLE clausula (id INTEGER PRIMARY KEY, texto TEXT)")
            c.exec_driver_sql("INSERT INTO clausula VALUES (1, 'Texto preservado')")
        ensure_document_benefit_columns(self.engine)
        with self.engine.begin() as c:
            self.assertEqual(c.exec_driver_sql("SELECT benefit_type FROM documento").scalar(), "PENSAO_MORTE")
            self.assertEqual(c.exec_driver_sql("SELECT texto FROM clausula").scalar(), "Texto preservado")

    def test_current_schema_needs_no_changes(self):
        Base.metadata.create_all(self.engine)
        with self.engine.begin() as c:
            before = c.exec_driver_sql("PRAGMA table_info(documento)").fetchall()
        ensure_document_benefit_columns(self.engine)
        with self.engine.begin() as c:
            self.assertEqual(c.exec_driver_sql("PRAGMA table_info(documento)").fetchall(), before)

    def test_missing_table_reports_initialization_order(self):
        with self.assertRaisesRegex(RuntimeError, "criada antes"):
            ensure_document_benefit_columns(self.engine)


if __name__ == "__main__":
    unittest.main()
