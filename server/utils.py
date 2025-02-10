from fastapi import Depends, Security, HTTPException, status
from fastapi.security import APIKeyHeader
from server.database import Session, get_session
from server.models import User

API_KEY_HEADER = APIKeyHeader(name="api-key")

def authenticate_user(
    api_key: str = Security(API_KEY_HEADER),
    session: Session = Depends(get_session),
):
    """Проверка существования пользователя"""
    user = session.query(User).filter(User.api_key == api_key).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication failed",
            headers={"api-key": ""},
        )

    return user
