from fastapi import Depends, HTTPException, Query
from typing import List
import sqlite3


def get_manager_dashboard_overview(current_user: str):
    """Controller for manager dashboard overview stats"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get manager ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (current_user,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        
        manager_id = manager['id']

        # Get team size
        cursor.execute(
            "SELECT COUNT(*) as count FROM team_members WHERE manager_id = ?",
            (manager_id,)
        )
        team_size = cursor.fetchone()['count']

        # Get total feedback given
        cursor.execute(
            "SELECT COUNT(*) as count FROM feedback WHERE manager_id = ?",
            (manager_id,)
        )
        total_feedback = cursor.fetchone()['count']

        # Get average team rating
        cursor.execute(
            "SELECT AVG(rating) as avg FROM feedback WHERE manager_id = ?",
            (manager_id,)
        )
        avg_rating = round(cursor.fetchone()['avg'] or 0, 1)

        # Get sentiment distribution
        cursor.execute(
            """SELECT 
                  sentiment, 
                  COUNT(*) as count
               FROM feedback
               WHERE manager_id = ?
               GROUP BY sentiment""",
            (manager_id,)
        )
        sentiment_distribution = {row['sentiment']: row['count'] for row in cursor.fetchall()}

        # Get recent feedback
        cursor.execute(
            """SELECT 
                  f.id, f.rating, f.sentiment, f.created_at,
                  e.name as employee_name,
                  e.id as employee_id
               FROM feedback f
               JOIN users e ON f.employee_id = e.id
               WHERE f.manager_id = ?
               ORDER BY f.created_at DESC
               LIMIT 5""",
            (manager_id,)
        )
        recent_feedback = [dict(row) for row in cursor.fetchall()]

        return {
            "team_size": team_size,
            "total_feedback_given": total_feedback,
            "avg_team_rating": avg_rating,
            "sentiment_distribution": sentiment_distribution,
            "recent_feedback": recent_feedback
        }

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def get_team_member_stats(current_user: str):
    """Controller for team member statistics"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get manager ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (current_user,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        
        manager_id = manager['id']

        # Get team members with stats
        cursor.execute(
            """SELECT 
                  e.id,
                  e.name,
                  e.email,
                  COUNT(f.id) as feedback_count,
                  AVG(f.rating) as avg_rating,
                  MAX(f.created_at) as last_feedback_date,
                  (SELECT sentiment FROM feedback 
                   WHERE employee_id = e.id 
                   ORDER BY created_at DESC LIMIT 1) as sentiment
               FROM users e
               JOIN team_members tm ON e.id = tm.employee_id
               LEFT JOIN feedback f ON e.id = f.employee_id AND f.manager_id = ?
               WHERE tm.manager_id = ?
               GROUP BY e.id, e.name, e.email
               ORDER BY e.name""",
            (manager_id, manager_id)
        )
        
        team_stats = []
        for row in cursor.fetchall():
            stats = dict(row)
            stats['avg_rating'] = round(stats['avg_rating'] or 0, 1) if stats['avg_rating'] else None
            team_stats.append(stats)

        return team_stats

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

def get_feedback_trends(time_range: str, current_user: str):
    """Controller for feedback trends analysis"""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get manager ID
        cursor.execute("SELECT id FROM users WHERE email = ?", (current_user,))
        manager = cursor.fetchone()
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        
        manager_id = manager['id']

        # Determine time grouping
        if time_range == "week":
            group_by = "strftime('%Y-%W', created_at)"
            time_format = "Week %W, %Y"
        elif time_range == "month":
            group_by = "strftime('%Y-%m', created_at)"
            time_format = "%b %Y"
        elif time_range == "quarter":
            group_by = "strftime('%Y', created_at) || '-' || ((strftime('%m', created_at)-1)/3)+1"
            time_format = "Q%q %Y"
        else:  # year
            group_by = "strftime('%Y', created_at)"
            time_format = "%Y"

        # Get feedback trends
        cursor.execute(
            f"""SELECT 
                  {group_by} as time_period,
                  COUNT(*) as feedback_count,
                  AVG(rating) as avg_rating
               FROM feedback
               WHERE manager_id = ?
               GROUP BY {group_by}
               ORDER BY time_period""",
            (manager_id,)
        )
        trends = [dict(row) for row in cursor.fetchall()]

        # Get sentiment trends
        cursor.execute(
            f"""SELECT 
                  {group_by} as time_period,
                  sentiment,
                  COUNT(*) as count
               FROM feedback
               WHERE manager_id = ?
               GROUP BY {group_by}, sentiment
               ORDER BY time_period""",
            (manager_id,)
        )
        sentiment_trends = [dict(row) for row in cursor.fetchall()]

        return {
            "time_format": time_format,
            "feedback_trends": trends,
            "sentiment_trends": sentiment_trends
        }

    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()
