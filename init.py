import sqlite3
from datetime import datetime, timedelta
import hashlib
import uuid
import random

def insert_dummy_data():
    conn = sqlite3.connect('database.db', isolation_level=None)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")

    def hash_password(password, salt=None):
        salt = salt or uuid.uuid4().hex
        return hashlib.sha256((password + salt).encode()).hexdigest(), salt

    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        c.executescript('''
            DELETE FROM feedback_acknowledgments;
            DELETE FROM feedback;
            DELETE FROM team_members;
            DELETE FROM users;
        ''')

        # Insert manager with more realistic data
        manager_salt = uuid.uuid4().hex
        manager_hash, manager_salt = hash_password('manager123', manager_salt)
        c.execute('''
            INSERT INTO users (name, email, password_hash, salt, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Kathirvel Manager', 'kathirvel.manager@company.com', manager_hash, manager_salt, 'manager', datetime.now().isoformat()))

        # Get manager ID
        c.execute('SELECT id FROM users WHERE email = ?', ('kathirvel.manager@company.com',))
        manager_id = c.fetchone()[0]

        # Team members with more realistic data
        team_members = [
            ('Ashwini S', 'ashwini.dev@company.com', 'Frontend Developer'),
            ('Vignesh A', 'vignesh.qa@company.com', 'QA Engineer'),
            ('Eshwar S', 'eshwar.analyst@company.com', 'Data Analyst'),
            ('Balaji M', 'balaji.devops@company.com', 'DevOps Engineer'),
            ('Sriram V', 'sriram.backend@company.com', 'Backend Developer'),
            ('Jairam V', 'jairam.design@company.com', 'UI/UX Designer'),
            ('Avinash PM', 'avinash.pm@company.com', 'Product Manager')
        ]

        # Sample strengths and improvement areas
        strengths = [
            "Excellent problem-solving skills and attention to detail",
            "Great team player with strong collaboration skills",
            "Consistently delivers high-quality work on time",
            "Shows exceptional initiative and creativity",
            "Excellent communication skills with stakeholders",
            "Strong technical expertise in their domain",
            "Very reliable and dependable team member"
        ]
        
        improvements = [
            "Could benefit from more proactive communication",
            "Would help to document work more thoroughly",
            "Could improve time estimation for tasks",
            "Would benefit from more code reviews",
            "Could participate more in team discussions",
            "Would help to mentor junior team members",
            "Could improve presentation skills"
        ]
        
        acknowledgment_comments = [
            "Thanks for the feedback, I'll work on these areas",
            "I appreciate the constructive feedback",
            "This is helpful, I'll implement these suggestions",
            "I understand the points for improvement",
            "Thanks for recognizing my strengths",
            "I'll focus on these improvement areas next quarter",
            "This feedback gives me clear direction"
        ]

        for name, email, position in team_members:
            # Insert user with salted password
            salt = uuid.uuid4().hex
            pass_hash, salt = hash_password('employee123', salt)
            c.execute('''
                INSERT INTO users (name, email, password_hash, salt, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, email, pass_hash, salt, 'employee', datetime.now().isoformat()))

            # Get employee ID
            c.execute('SELECT id FROM users WHERE email = ?', (email,))
            employee_id = c.fetchone()[0]

            # Assign to manager
            c.execute('''
                INSERT INTO team_members (manager_id, employee_id, assigned_at)
                VALUES (?, ?, ?)
            ''', (manager_id, employee_id, datetime.now().isoformat()))

            # Insert sample feedback for each employee (3-5 items per employee)
            sentiments = ['positive', 'neutral', 'negative']
            feedback_count = random.randint(3, 5)
            
            for i in range(feedback_count):
                # Create feedback with random dates in the past 6 months
                feedback_date = datetime.now() - timedelta(days=random.randint(1, 180))
                updated_date = feedback_date + timedelta(days=random.randint(1, 30))
                
                c.execute('''
                    INSERT INTO feedback (
                        manager_id, employee_id, strengths, areas_to_improve, 
                        sentiment, rating, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    manager_id,
                    employee_id,
                    f"{random.choice(strengths)}. Specifically in your role as {position}, you've shown great progress.",
                    f"{random.choice(improvements)}. As a {position}, focusing here would help your growth.",
                    random.choice(sentiments),
                    random.randint(3, 5),  # Rating between 3-5
                    feedback_date.isoformat(),
                    updated_date.isoformat()
                ))

                # Get the feedback ID
                feedback_id = c.lastrowid

                # Mark some feedback as acknowledged (about 70% chance)
                if random.random() < 0.7:
                    ack_date = updated_date + timedelta(days=random.randint(1, 14))
                    c.execute('''
                        INSERT INTO feedback_acknowledgments (
                            feedback_id, employee_id, acknowledged_at, comment
                        )
                        VALUES (?, ?, ?, ?)
                    ''', (
                        feedback_id, 
                        employee_id, 
                        ack_date.isoformat(),
                        random.choice(acknowledgment_comments)
                    ))

        print(f"[{datetime.now().isoformat()}] Dummy data inserted successfully.")
        print(f"Manager login: kathirvel.manager@company.com / manager123")
        print(f"Employee login: ashwini.dev@company.com / employee123")
        print(f"Total employees created: {len(team_members)}")
        print(f"Each employee has 3-5 feedback items, with ~70% acknowledged")

    except sqlite3.Error as e:
        print(f"[{datetime.now().isoformat()}] Error inserting dummy data: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    insert_dummy_data()