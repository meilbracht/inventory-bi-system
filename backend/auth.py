from passlib.context import CryptContext
from fastapi import HTTPException, status

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    return pwd.verify(p, hashed)

def require_role(user_role: str, allowed: set[str]):
    if user_role not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized for this action."
        )
