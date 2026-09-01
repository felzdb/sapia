import secrets
import smtplib
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone


from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from .email_service import FRONTEND_URL, send_confirmation_email

from .storage import reset_temp_storage
from .documents import router as documents_router

from .auth import (
    SESSIONS,
    create_access_token,
    get_bearer_token,
    get_current_user,
    get_db,
    hash_password,
    revoke_token,
    verify_password,
)
from .database import (Base, SessionLocal, engine, ensure_user_confirmed_at_column, reset_database_file)
from .models import ConfirmationToken, User
from .schemas import (
    HealthResponse,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)


DEMO_EMAIL = "admin@sapia.com"
DEMO_PASSWORD = "Sapia@123"


def seed_demo_user() -> None:
    with SessionLocal() as db:
        existing = db.scalar(select(User).where(User.email == DEMO_EMAIL))

        if existing:
            return

        user = User(
            name="Administrador SAPIA",
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            role="ADMINISTRADOR",
            status="ATIVO",
        )

        db.add(user)
        db.commit()


def password_is_strong(password: str) -> bool:
    return (
        len(password) >= 8
        and any(char.isupper() for char in password)
        and any(char.islower() for char in password)
        and any(char.isdigit() for char in password)
        and any(not char.isalnum() for char in password)
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    SESSIONS.clear()
    reset_database_file()
    reset_temp_storage()
    Base.metadata.create_all(bind=engine)
    ensure_user_confirmed_at_column()
    seed_demo_user()

    yield

    SESSIONS.clear()
    reset_temp_storage()


app = FastAPI(
    title="SAPIA API",
    description="Backend inicial do protótipo SAPIA.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)


@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "service": "SAPIA API",
    }


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    name = payload.name.strip()
    email = str(payload.email).lower()

    if len(name) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O nome completo deve ter entre 3 e 100 caracteres.",
        )

    if payload.password != payload.password_confirmation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="As senhas informadas não coincidem.",
        )

    if not password_is_strong(payload.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A senha deve conter no mínimo 8 caracteres, "
                "letras maiúsculas, minúsculas e números."
            ),
        )

    existing_user = db.scalar(select(User).where(User.email == email))

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail já está cadastrado.",
        )

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(payload.password),
        role="USUARIO",
        status="PENDENTE",
    )

    db.add(user)
    db.flush()

    confirmation_token = ConfirmationToken(
        token=secrets.token_urlsafe(32),
        type="CONFIRMACAO_CADASTRO",
        expires_at=datetime.utcnow() + timedelta(hours=24),
        used=False,
        user_id=user.id,
    )

    db.add(confirmation_token)

    try:
        send_confirmation_email(email, confirmation_token.token)
    except (RuntimeError, smtplib.SMTPException, OSError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Não foi possível enviar o e-mail de confirmação. "
                "Tente novamente."
            ),
        ) from exc

    db.commit()
    db.refresh(user)

    return user


@app.get("/auth/confirm")
def confirm_account(token: str, db: Session = Depends(get_db)):
    confirmation_token = db.scalar(
        select(ConfirmationToken).where(
            ConfirmationToken.token == token,
            ConfirmationToken.type == "CONFIRMACAO_CADASTRO",
        )
    )

    if confirmation_token is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token de confirmação inválido.",
        )

    if confirmation_token.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este token de confirmação já foi utilizado.",
        )

    if confirmation_token.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O token de confirmação expirou.",
        )

    user = db.get(User, confirmation_token.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    user.status = "ATIVO"
    user.confirmed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    confirmation_token.used = True

    db.commit()

    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Conta confirmada - SAPIA</title>
            <style>
                * {
                    box-sizing: border-box;
                }

                body {
                    margin: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 24px;
                    font-family: Arial, sans-serif;
                    background: #f5f7fb;
                    color: #172033;
                }

                .card {
                    width: 100%;
                    max-width: 480px;
                    padding: 40px;
                    background: white;
                    border: 1px solid #ddd;
                    border-radius: 12px;
                    text-align: center;
                }

                .logo {
                    width: 58px;
                    height: 58px;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 10px;
                    background: #263b77;
                    color: white;
                    font-size: 25px;
                    font-weight: bold;
                }

                h1 {
                    margin: 0 0 12px;
                    font-size: 26px;
                }

                p {
                    margin: 0 0 28px;
                    color: #697287;
                    line-height: 1.5;
                }

                a {
                    display: block;
                    width: 100%;
                    padding: 13px;
                    border-radius: 6px;
                    background: #263b77;
                    color: white;
                    text-decoration: none;
                    font-weight: bold;
                }

                a:hover {
                    background: #1f3267;
                }
            </style>
        </head>

        <body>
            <main class="card">
                <div class="logo">S</div>

                <h1>Conta confirmada com sucesso!</h1>

                <p>
                    Seu cadastro no SAPIA foi ativado.
                    Agora você já pode acessar o sistema com seu e-mail e senha.
                </p>

                <a href="__FRONTEND_URL__">
                    Ir para o SAPIA
                </a>
            </main>
        </body>
        </html>
        """.replace("__FRONTEND_URL__", FRONTEND_URL),
        status_code=200,
    )


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Este endereço de e-mail não está cadastrado no sistema.",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "E-mail e/ou senha incorretos. "
                "Tente novamente ou recupere sua senha."
            ),
        )

    if user.status != "ATIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Sua conta ainda não foi confirmada. "
                "Verifique seu e-mail e confirme o cadastro antes de entrar."
            ),
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@app.get("/auth/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/auth/logout", status_code=204)
def logout(token: str = Depends(get_bearer_token)):
    revoke_token(token)
