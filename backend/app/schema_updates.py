"""Atualizações compatíveis com os bancos SQLite anteriores do SAPIA."""


def ensure_document_benefit_columns(db_engine) -> None:
    """Adiciona somente colunas ausentes, preservando os registros existentes."""
    required_columns = {
        "benefit_type": "VARCHAR(100)",
        "benefit_confidence": "FLOAT",
        "benefit_original_type": "VARCHAR(100)",
        "benefit_corrected_manually": "BOOLEAN NOT NULL DEFAULT 0",
    }

    with db_engine.begin() as connection:
        columns = connection.exec_driver_sql(
            "PRAGMA table_info(documento)"
        ).fetchall()

        if not columns:
            raise RuntimeError(
                "A tabela documento deve ser criada antes da atualização."
            )

        column_names = {column[1] for column in columns}

        # Os nomes e tipos abaixo vêm da lista fixa definida neste módulo.
        for name, definition in required_columns.items():
            if name not in column_names:
                connection.exec_driver_sql(
                    f"ALTER TABLE documento ADD COLUMN {name} {definition}"
                )
