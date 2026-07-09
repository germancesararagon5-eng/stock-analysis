import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import MagicLinkToken, User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    return user


def send_magic_link(email: str, token: str) -> bool:
    if not settings.smtp_host:
        return False
    link = f"{settings.app_url}/api/auth/magic-link/verify?token={token}"
    msg = MIMEText(
        f"Inicia sesión en Stock Analysis haciendo clic en este enlace:\n\n{link}\n\n"
        f"Este enlace expira en 15 minutos. Si no solicitaste este acceso, ignorá este mensaje."
    )
    msg["Subject"] = "Stock Analysis — Link mágico de inicio de sesión"
    msg["From"] = settings.smtp_from
    msg["To"] = email
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_pass)
            server.sendmail(settings.smtp_from, [email], msg.as_string())
        return True
    except Exception:
        return False


def create_magic_link_token(email: str, db: Session) -> str:
    token = secrets.token_urlsafe(48)
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.add(MagicLinkToken(email=email, token=token, expires_at=expires))
    db.commit()
    return token


def verify_magic_link_token(token: str, db: Session) -> str | None:
    record = db.query(MagicLinkToken).filter(
        MagicLinkToken.token == token,
        MagicLinkToken.used == False,
        MagicLinkToken.expires_at > datetime.now(timezone.utc),
    ).first()
    if not record:
        return None
    record.used = True
    db.commit()
    return record.email
