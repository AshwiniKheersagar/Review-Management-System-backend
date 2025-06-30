from fastapi import Depends, HTTPException
import sqlite3
from app.utils.auth import get_current_user

def get_feedback_history(employee_id: int, current_user: str):
    """Controller for getting feedback history"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verify current user
        cursor.execute("SELECT id, role FROM users WHERE email = ?", (current_user,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Authorization checks
        if user['role'] == 'employee' and user['id'] != employee_id:
            raise HTTPException(status_code=403, detail="Not authorized")

        if user['role'] == 'manager':
            cursor.execute(
                "SELECT 1 FROM team_members WHERE manager_id = ? AND employee_id = ?",
                (user['id'], employee_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="Not authorized")

        # Get feedback history
        cursor.execute('''
            SELECT f.id, f.strengths, f.areas_to_improve, f.sentiment, 
                   f.rating, f.created_at, f.is_acknowledged, u.name as manager_name
            FROM feedback f
            JOIN users u ON f.manager_id = u.id
            WHERE f.employee_id = ?
            ORDER BY f.created_at DESC
        ''', (employee_id,))
        
        return [dict(feedback) for feedback in cursor.fetchall()]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def get_employee_details(employee_id: int, current_user: str):
    """Controller for getting employee details"""
    try:
        if employee_id <= 0:
            raise HTTPException(status_code=400, detail="Employee ID must be positive")

        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, email, role FROM users WHERE id = ? AND role = 'employee'",
            (employee_id,)
        )
        employee = cursor.fetchone()
        
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        return dict(employee)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def get_employee_feedback(employee_id: int, current_user: str):
    """Controller for getting employee feedback"""
    try:
        if employee_id <= 0:
            raise HTTPException(status_code=400, detail="Employee ID must be positive")

        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, role FROM users WHERE email = ?", (current_user,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user['role'] == 'employee' and user['id'] != employee_id:
            raise HTTPException(status_code=403, detail="Not authorized to view this feedback")

        if user['role'] == 'manager':
            cursor.execute(
                "SELECT 1 FROM team_members WHERE manager_id = ? AND employee_id = ?",
                (user['id'], employee_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=403, detail="Not authorized to view this employee's feedback")

        cursor.execute('''
            SELECT 
                f.id,
                f.strengths,
                f.areas_to_improve,
                f.sentiment,
                f.rating,
                f.created_at,
                u.name as manager_name,
                u.email as manager_email,
                CASE WHEN fa.id IS NOT NULL THEN 1 ELSE 0 END as is_acknowledged
            FROM feedback f
            JOIN users u ON f.manager_id = u.id
            LEFT JOIN feedback_acknowledgments fa ON f.id = fa.feedback_id AND fa.employee_id = ?
            WHERE f.employee_id = ?
            ORDER BY f.created_at DESC
        ''', (employee_id, employee_id))
        
        return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()