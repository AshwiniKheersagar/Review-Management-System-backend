from fastapi import Depends, HTTPException, Query
from typing import List
import sqlite3
from datetime import datetime, timedelta


def get_employee_dashboard_stats(current_user: str):
    """Controller for employee dashboard statistics"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get employee ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (current_user,))
        employee = cursor.fetchone()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        employee_id = employee['id']

        # Get total feedback count
        cursor.execute(
            "SELECT COUNT(*) as count FROM feedback WHERE employee_id = ?",
            (employee_id,)
        )
        total_feedback = cursor.fetchone()['count']

        # Get average rating
        cursor.execute(
            "SELECT AVG(rating) as avg FROM feedback WHERE employee_id = ?",
            (employee_id,)
        )
        avg_rating = round(cursor.fetchone()['avg'] or 0, 1)

        # Get positive feedback count
        cursor.execute(
            """SELECT COUNT(*) as count 
               FROM feedback 
               WHERE employee_id = ? AND sentiment = 'positive'""",
            (employee_id,)
        )
        positive_count = cursor.fetchone()['count']

        # Get acknowledged feedback count
        cursor.execute(
            """SELECT COUNT(*) as count 
               FROM feedback 
               WHERE employee_id = ? AND is_acknowledged = 1""",
            (employee_id,)
        )
        acknowledged_count = cursor.fetchone()['count']

        # Get recent feedback (last 5)
        cursor.execute(
            """SELECT f.*, u.name as manager_name, fa.comment as acknowledgment_comment
               FROM feedback f
               JOIN users u ON f.manager_id = u.id
               LEFT JOIN feedback_acknowledgments fa ON f.id = fa.feedback_id
               WHERE f.employee_id = ?
               ORDER BY f.created_at DESC
               LIMIT 5""",
            (employee_id,)
        )
        recent_feedback = [dict(row) for row in cursor.fetchall()]

        return {
            "total_feedback": total_feedback,
            "avg_rating": avg_rating,
            "positive_count": positive_count,
            "acknowledged_count": acknowledged_count,
            "recent_feedback": recent_feedback
        }

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def get_employee_feedback_timeline(time_filter: str, current_user: str):
    """Controller for employee feedback timeline"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get employee ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (current_user,))
        employee = cursor.fetchone()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        employee_id = employee['id']

        # Base query
        query = """
            SELECT 
                f.id,
                f.strengths,
                f.areas_to_improve,
                f.sentiment,
                f.rating,
                f.created_at,
                f.is_acknowledged,
                u.name as manager_name,
                fa.comment as acknowledgment_comment
            FROM feedback f
            JOIN users u ON f.manager_id = u.id
            LEFT JOIN feedback_acknowledgments fa ON f.id = fa.feedback_id
            WHERE f.employee_id = ?
        """

        # Add time filter
        time_conditions = {
            "month": "AND f.created_at >= datetime('now', '-1 month')",
            "quarter": "AND f.created_at >= datetime('now', '-3 months')",
            "year": "AND f.created_at >= datetime('now', '-1 year')",
            "all": ""
        }
        query += f" {time_conditions[time_filter]} ORDER BY f.created_at DESC"

        cursor.execute(query, (employee_id,))
        return [dict(row) for row in cursor.fetchall()]

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()