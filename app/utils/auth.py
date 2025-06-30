import jwt
import datetime
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import uuid
from typing import Tuple, Optional

SECRET_KEY = "my_secret"  # Use `os.getenv("SECRET_KEY")` in production
ALGORITHM = "HS256"
security = HTTPBearer()

def create_token(email: str,employeeID:int,name: str, role: str) -> str:
    payload = {
        "sub": email,
        "name": name,
        "employeeID":employeeID,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    token = credentials.credentials
    return verify_token(token)


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """Hash a password with a salt (or generate a new salt if None)."""
    salt = salt or uuid.uuid4().hex
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return hashed, salt