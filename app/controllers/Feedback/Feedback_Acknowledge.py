from fastapi import HTTPException
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional


def acknowledge_feedback(
    feedback_id: int,
    employee_email: str,
    comment: Optional[str] = None
) -> Dict:
    """Business logic for acknowledging feedback"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get employee info
        cursor.execute("SELECT id, name FROM users WHERE email = ?", (employee_email,))
        employee = cursor.fetchone()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # Verify feedback exists and is for this employee
        cursor.execute(
            """SELECT f.*, u.name as manager_name 
               FROM feedback f
               JOIN users u ON f.manager_id = u.id
               WHERE f.id = ? AND f.employee_id = ?""",
            (feedback_id, employee['id'])
        )
        feedback = cursor.fetchone()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found or not authorized")

        # Check if already acknowledged
        if feedback['is_acknowledged']:
            raise HTTPException(status_code=400, detail="Feedback already acknowledged")

        # Create acknowledgment record
        cursor.execute(
            """
            INSERT INTO feedback_acknowledgments (
                feedback_id,
                employee_id,
                comment,
                acknowledged_at
            ) VALUES (?, ?, ?, datetime('now'))
            RETURNING id, acknowledged_at
            """,
            (feedback_id, employee['id'], comment)
        )
        ack = cursor.fetchone()
        
        # Update the feedback acknowledged status
        cursor.execute(
            "UPDATE feedback SET is_acknowledged = 1 WHERE id = ?",
            (feedback_id,)
        )

        # Verify the update
        cursor.execute("SELECT is_acknowledged FROM feedback WHERE id = ?", (feedback_id,))
        updated_status = cursor.fetchone()
        if not updated_status or not updated_status['is_acknowledged']:
            raise HTTPException(status_code=500, detail="Failed to update acknowledgment status")

        # Prepare response
        acknowledgment = {
            "id": ack['id'],
            "feedback_id": feedback_id,
            "employee_id": employee['id'],
            "employee_name": employee['name'],
            "manager_name": feedback['manager_name'],
            "comment": comment,
            "acknowledged_at": ack['acknowledged_at'],
            "is_acknowledged": True,
            "feedback_details": {
                "strengths": feedback['strengths'],
                "areas_to_improve": feedback['areas_to_improve'],
                "sentiment": feedback['sentiment'],
                "rating": feedback['rating'],
                "created_at": feedback['created_at'],
                "is_acknowledged": True
            }
        }

        conn.commit()
        return acknowledgment

    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def get_feedback_acknowledgment(
    feedback_id: int, 
    current_user_email: str
) -> Dict:
    """Business logic for retrieving feedback acknowledgment"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verify feedback exists and user has access
        cursor.execute('''
            SELECT fa.*, u.name as employee_name
            FROM feedback_acknowledgments fa
            JOIN feedback f ON fa.feedback_id = f.id
            JOIN users u ON fa.employee_id = u.id
            WHERE fa.feedback_id = ? AND (f.employee_id = (
                SELECT id FROM users WHERE email = ?
            ) OR f.manager_id = (
                SELECT id FROM users WHERE email = ?
            ))
        ''', (feedback_id, current_user_email, current_user_email))

        acknowledgment = cursor.fetchone()
        if not acknowledgment:
            raise HTTPException(status_code=404, detail="Not Acknowledged")

        return dict(acknowledgment)
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()