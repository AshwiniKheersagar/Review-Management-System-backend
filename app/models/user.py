import sqlite3
import hashlib
import uuid
from typing import Optional, Tuple
from datetime import datetime
from app.utils.auth import hash_password 
from fastapi import HTTPException
from typing import List, Dict  # Add this import at the top of user.py

DB_NAME = "database.db"

def init_db():
    """Initialize the database with all tables"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Enable foreign key constraints
    c.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Users table
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            role TEXT CHECK(role IN ('manager', 'employee')) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT 1
        )''')

        # Team members relationship table
        c.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manager_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(manager_id, employee_id)
        )''')

        # Feedback table
        c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manager_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            strengths TEXT NOT NULL,
            areas_to_improve TEXT NOT NULL,
            sentiment TEXT CHECK(sentiment IN ('positive', 'neutral', 'negative')) NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            is_private BOOLEAN DEFAULT 0,
            is_acknowledged BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE
        )''')

        # Feedback acknowledgments
        c.execute('''
        CREATE TABLE IF NOT EXISTS feedback_acknowledgments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            feedback_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            acknowledged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            comment TEXT,
            FOREIGN KEY (feedback_id) REFERENCES feedback(id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(feedback_id, employee_id)
        )''')

        # Create indexes for better performance
        c.execute('CREATE INDEX IF NOT EXISTS idx_feedback_employee ON feedback(employee_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_feedback_manager ON feedback(manager_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_team_members_manager ON team_members(manager_id)')
        
        conn.commit()
        print(f"[{datetime.now().isoformat()}] Database initialized successfully")
        
    except sqlite3.Error as e:
        print(f"[{datetime.now().isoformat()}] Database initialization failed: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[Tuple]:
    """Get user by email"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()
    return user



def get_feedback_history(manager_id: int, employee_id: int) -> List[Dict]:
    """Get feedback history for an employee from a specific manager"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all feedback for employee from this manager
        cursor.execute(
            """
            SELECT 
                f.id,
                f.strengths,
                f.areas_to_improve,
                f.sentiment,
                f.rating,
                f.created_at,
                f.updated_at,
                CASE WHEN fa.id IS NOT NULL THEN 1 ELSE 0 END as is_acknowledged,
                fa.comment as acknowledgment_comment,
                fa.acknowledged_at
            FROM feedback f
            LEFT JOIN feedback_acknowledgments fa ON f.id = fa.feedback_id
            WHERE f.manager_id = ? AND f.employee_id = ?
            ORDER BY f.created_at DESC
            """,
            (manager_id, employee_id)
        )
        feedback_list = cursor.fetchall()

        return [dict(feedback) for feedback in feedback_list]

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
        
if __name__ == '__main__':
    init_db()