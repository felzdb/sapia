from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "sapia_demo.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def ensure_user_confirmed_at_column() -> None:
    with engine.begin() as connection:
        columns = connection.exec_driver_sql(
            "PRAGMA table_info(usuario)"
        ).fetchall()

        column_names = {column[1] for column in columns}

        if "confirmed_at" not in column_names:
            connection.exec_driver_sql(
                "ALTER TABLE usuario ADD COLUMN confirmed_at DATETIME"
            )


def reset_database_file():
    engine.dispose()

    if DB_PATH.exists():
        DB_PATH.unlink()
