from fastapi import APIRouter, Depends, HTTPException, Query, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.services.auth_service import (
    create_access_token,
    create_magic_link_token,
    get_current_user,
    hash_password,
    send_magic_link,
    verify_magic_link_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str


class GoogleAuthRequest(BaseModel):
    id_token: str


@router.get("/google/config")
def google_config():
    return {
        "enabled": bool(settings.google_client_id),
        "client_id": settings.google_client_id or "",
    }


@router.post("/google", response_model=TokenResponse)
def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    if not settings.google_client_id:
        raise HTTPException(status_code=400, detail="Google OAuth no configurado")

    try:
        info = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
        email = info.get("email", "")
        name = info.get("name", email.split("@")[0])
        sub = info.get("sub", "")

        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                username=name.replace(" ", "_") + "_" + sub[:6],
                email=email,
                password_hash=hash_password(sub),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return TokenResponse(access_token=create_access_token(user.id))

    except ValueError:
        raise HTTPException(status_code=401, detail="Token de Google invalido")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email ya registrado")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contrasena incorrectos")
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/magic-link")
def request_magic_link(email: str = Query(...), db: Session = Depends(get_db)):
    token = create_magic_link_token(email, db)
    sent = send_magic_link(email, token)
    if not sent:
        token_value = token
        return {
            "sent": False,
            "message": "SMTP no configurado. Compartí este link directamente:",
            "debug_link": f"{settings.app_url}/api/auth/magic-link/verify?token={token_value}",
        }
    return {"sent": True, "message": "Link mágico enviado al email"}


@router.get("/magic-link/verify", response_model=TokenResponse)
def verify_magic_link(token: str = Query(...), db: Session = Depends(get_db)):
    email = verify_magic_link_token(token, db)
    if not email:
        raise HTTPException(status_code=400, detail="Token invalido o expirado")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        username = email.split("@")[0].replace(".", "_")[:50]
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(token),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/demo", response_model=TokenResponse)
def demo_login(db: Session = Depends(get_db)):
    import secrets as sec
    suffix = sec.token_hex(4)
    username = f"demo_{suffix}"
    email = f"{username}@demo.local"
    password = sec.token_hex(16)

    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        is_demo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, username=current_user.username, email=current_user.email)
