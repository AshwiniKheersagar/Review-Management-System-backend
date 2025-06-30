from fastapi import HTTPException
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

def get_unassigned_employees(manager_email: str) -> List[Dict]:
    """Helper function to get employees not assigned to this specific manager"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Verify user is manager and get manager_id
        cursor.execute("SELECT id, role FROM users WHERE email = ?", (manager_email,))
        user = cursor.fetchone()
        if not user or user['role'] != 'manager':
            raise HTTPException(status_code=403, detail="Only managers can access this endpoint")
        manager_id = user['id']

        # Get employees not assigned to THIS manager (may be assigned to others)
        cursor.execute('''
            SELECT u.id, u.name, u.email, u.role
            FROM users u
            WHERE u.role = 'employee'
            AND NOT EXISTS (
                SELECT 1 FROM team_members tm 
                WHERE tm.employee_id = u.id AND tm.manager_id = ?
            )
            ORDER BY u.name
        ''', (manager_id,))
        employees = cursor.fetchall()

        return [dict(employee) for employee in employees]

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def get_manager_teams(manager_email: str) -> List[Dict]:
    """Get all employees in a manager's team"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row  # This makes rows behave like dictionaries
        cursor = conn.cursor()

        # Get manager ID and verify role
        cursor.execute("SELECT id, role FROM users WHERE email = ?", (manager_email,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        if manager['role'] != 'manager':
            raise HTTPException(status_code=403, detail="Only managers can view teams")
        manager_id = manager['id']

        # Get all employees in manager's team
        cursor.execute(
            """
            SELECT u.id, u.name, u.email, u.role, tm.assigned_at
            FROM team_members tm
            JOIN users u ON tm.employee_id = u.id
            WHERE tm.manager_id = ?
            ORDER BY u.name
            """,
            (manager_id,)
        )
        team_members = cursor.fetchall()

        # Convert to list of dictionaries and add feedback count
        result = []
        for member in team_members:
            member_dict = dict(member)  # Convert Row to dictionary
            cursor.execute(
                "SELECT COUNT(*) FROM feedback WHERE employee_id = ? AND manager_id = ?",
                (member_dict['id'], manager_id)
            )
            feedback_count = cursor.fetchone()[0]
            member_dict['feedback_count'] = feedback_count
            result.append(member_dict)

        return result

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def add_team_member(employee_email: str, manager_email: str) -> Dict:
    """Add an employee to a manager's team"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Get manager ID and verify role
        cursor.execute("SELECT id, role FROM users WHERE email = ?", (manager_email,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        if manager[1] != 'manager':
            raise HTTPException(status_code=403, detail="Only managers can create teams")
        manager_id = manager[0]

        # Get employee ID and verify role
        cursor.execute("SELECT id, role FROM users WHERE email = ?", (employee_email,))
        employee = cursor.fetchone()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        if employee[1] != 'employee':
            raise HTTPException(status_code=400, detail="Can only add employees to a team")
        employee_id = employee[0]

        # Check if already in team
        cursor.execute(
            "SELECT 1 FROM team_members WHERE manager_id = ? AND employee_id = ?",
            (manager_id, employee_id)
        )
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Employee already in your team")

        # Add to team
        cursor.execute(
            "INSERT INTO team_members (manager_id, employee_id, assigned_at) VALUES (?, ?, ?)",
            (manager_id, employee_id, datetime.now())
        )

        conn.commit()
        return {
            "message": "Employee added to team successfully",
            "employee_id": employee_id,
            "manager_id": manager_id
        }

    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def remove_team_member(manager_email: str, employee_id: int) -> Dict:
    """Remove an employee from a manager's team"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Get manager ID and verify role
        cursor.execute("SELECT id, role FROM users WHERE email = ?", (manager_email,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        if manager[1] != 'manager':
            raise HTTPException(status_code=403, detail="Only managers can modify teams")
        manager_id = manager[0]

        # Check if employee exists
        cursor.execute("SELECT 1 FROM users WHERE id = ? AND role = 'employee'", (employee_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Employee not found")

        # Check if employee is in manager's team
        cursor.execute(
            "SELECT 1 FROM team_members WHERE manager_id = ? AND employee_id = ?",
            (manager_id, employee_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Employee not in your team")

        # Remove from team
        cursor.execute(
            "DELETE FROM team_members WHERE manager_id = ? AND employee_id = ?",
            (manager_id, employee_id)
        )

        conn.commit()
        return {"message": "Employee removed from team successfully"}

    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()