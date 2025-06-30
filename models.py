import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('database.db', isolation_level=None)  # Auto-commit mode
    c = conn.cursor()
    
    # Enable foreign key constraints
    c.execute("PRAGMA foreign_keys = ON")
    
    print(f"[{datetime.now().isoformat()}] Initializing database...")
    
    try:
        # Create tables with improved schema
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

        c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            manager_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            strengths TEXT NOT NULL,
            areas_to_improve TEXT NOT NULL,
            sentiment TEXT CHECK(sentiment IN ('positive', 'neutral', 'negative')) NOT NULL,
            is_private BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES users(id) ON DELETE CASCADE
        )''')

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

        # You’ll often need to fetch all feedback given to a specific employee.
        # Without an index, SQLite must scan the whole feedback table.
        c.execute('CREATE INDEX IF NOT EXISTS idx_feedback_employee ON feedback(employee_id)')

        # Useful when fetching feedback submitted by a manager.
        c.execute('CREATE INDEX IF NOT EXISTS idx_feedback_manager ON feedback(manager_id)')

        # You'll often need to list team members of a manager.
        c.execute('CREATE INDEX IF NOT EXISTS idx_team_members_manager ON team_members(manager_id)')
        
        print(f"[{datetime.now().isoformat()}] Database initialized successfully")
        
    except sqlite3.Error as e:
        print(f"[{datetime.now().isoformat()}] Database initialization failed: {e}")
        
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()