from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

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
from .database import Base, SessionLocal, engine
from .models import User
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
    Base.metadata.create_all(bind=engine)
    seed_demo_user()

    yield

    SESSIONS.clear()


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
                "A senha deve ter no mínimo 8 caracteres, incluindo "
                "letra maiúscula, minúscula, número e caractere especial."
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
    db.commit()
    db.refresh(user)

    return user


@app.post("/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email))

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail e/ou senha incorretos.",
        )

    if user.status != "ATIVO":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário sem permissão de acesso.",
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
