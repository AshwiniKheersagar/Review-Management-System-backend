from fastapi import HTTPException
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from app.models.user import get_user_by_email
from app.models.user import get_feedback_history
from pydantic import BaseModel


class FeedbackUpdate(BaseModel):
    strengths: str
    areas_to_improve: str
    sentiment: str
    rating: int

class FeedbackCreate(BaseModel):
    employee_id: str
    strengths: str
    areas_to_improve: str
    sentiment: str
    rating: int


def submit_feedback(feedback_data: FeedbackCreate, manager_email: str) -> Dict:
    """Submit new feedback for an employee"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Validate manager exists
        cursor.execute("SELECT id FROM users WHERE email = ? AND role = 'manager'", (manager_email,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found or invalid role")
        manager_id = manager['id']

        # Validate employee exists
        cursor.execute("SELECT id FROM users WHERE email = ? AND role = 'employee'", (feedback_data.employee_id,))
        employee = cursor.fetchone()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found or invalid role")
        employee_id = employee['id']

        # Validate authorization
        cursor.execute(
            "SELECT 1 FROM team_members WHERE manager_id = ? AND employee_id = ?",
            (manager_id, employee_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Not authorized to give feedback to this employee")

        # Validate sentiment value
        valid_sentiments = ['positive', 'neutral', 'negative']
        if feedback_data.sentiment not in valid_sentiments:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid sentiment: '{feedback_data.sentiment}'. Must be one of: {', '.join(valid_sentiments)}"
            )

        # Validate rating (1-5)
        if not 1 <= feedback_data.rating <= 5:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid rating: {feedback_data.rating}. Must be between 1 and 5"
            )

        # Insert feedback
        cursor.execute(
            """
            INSERT INTO feedback (
                manager_id,
                employee_id,
                strengths,
                areas_to_improve,
                sentiment,
                rating,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                manager_id,
                employee_id,
                feedback_data.strengths.strip(),
                feedback_data.areas_to_improve.strip(),
                feedback_data.sentiment,
                feedback_data.rating
            )
        )
        feedback_id = cursor.lastrowid

        # Return the created feedback
        cursor.execute(
            """
            SELECT f.*, u1.email as manager_email, u2.email as employee_email
            FROM feedback f
            JOIN users u1 ON f.manager_id = u1.id
            JOIN users u2 ON f.employee_id = u2.id
            WHERE f.id = ?
            """,
            (feedback_id,)
        )
        feedback = cursor.fetchone()

        conn.commit()
        return dict(feedback)

    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def update_feedback_db(feedback_id: int, feedback_data: FeedbackUpdate, manager_email: str) -> Dict:
    """Update existing feedback"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Validate manager exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (manager_email,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        manager_id = manager['id']

        # Verify feedback exists and belongs to this manager
        cursor.execute(
            "SELECT * FROM feedback WHERE id = ? AND manager_id = ?",
            (feedback_id, manager_id)
        )
        feedback = cursor.fetchone()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found or not authorized")

        # Validate sentiment value
        valid_sentiments = ['positive', 'neutral', 'negative']
        if feedback_data.sentiment not in valid_sentiments:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid sentiment: '{feedback_data.sentiment}'. Must be one of: {', '.join(valid_sentiments)}"
            )

        # Validate rating (1-5)
        if not 1 <= feedback_data.rating <= 5:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid rating: {feedback_data.rating}. Must be between 1 and 5"
            )

        # Update feedback
        cursor.execute(
            """
            UPDATE feedback SET
                strengths = ?,
                areas_to_improve = ?,
                sentiment = ?,
                rating = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (
                feedback_data.strengths.strip(),
                feedback_data.areas_to_improve.strip(),
                feedback_data.sentiment,
                feedback_data.rating,
                feedback_id
            )
        )

        # Return updated feedback
        cursor.execute(
            """
            SELECT f.*, u1.email as manager_email, u2.email as employee_email
            FROM feedback f
            JOIN users u1 ON f.manager_id = u1.id
            JOIN users u2 ON f.employee_id = u2.id
            WHERE f.id = ?
            """,
            (feedback_id,)
        )
        updated_feedback = cursor.fetchone()

        conn.commit()
        return dict(updated_feedback)

    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
              
def delete_feedback(feedback_id: int, manager_email: str) -> Dict:
    """Delete feedback"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verify manager exists and get ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (manager_email,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        manager_id = manager['id']

        # Verify feedback exists and belongs to this manager
        cursor.execute(
            "SELECT * FROM feedback WHERE id = ? AND manager_id = ?",
            (feedback_id, manager_id)
        )
        feedback = cursor.fetchone()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found or not authorized")

        # Delete feedback
        cursor.execute("DELETE FROM feedback WHERE id = ?", (feedback_id,))

        conn.commit()
        return {"message": "Feedback deleted successfully"}

    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

