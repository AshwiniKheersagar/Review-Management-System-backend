from fastapi import HTTPException
from app.models.user import get_user_by_email
from app.utils.auth import create_token, hash_password
import sqlite3

def create_user(name: str, email: str, password: str, role: str = "employee"):
    """Create a new user"""
    password_hash, salt = hash_password(password)
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (name, email, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
            (name, email, password_hash, salt, role)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Email already exists")
    finally:
        conn.close()

def login_user(email: str, password: str) -> str:
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    
    stored_hash, salt = user[3], user[4]  # password_hash, salt
    new_hash, _ = hash_password(password, salt)
    
    if new_hash != stored_hash:
        raise HTTPException(status_code=400, detail="Incorrect password")
    
    # Get name and role from user tuple (assuming index 1 is name and index 5 is role)
    employeeID=user[0]
    name = user[1]
    role = user[5]
    return create_token(email,employeeID, name, role)