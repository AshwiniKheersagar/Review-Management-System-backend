import sqlite3
from tabulate import tabulate

def display_all_data():
    # Connect to the database
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    try:
        # Get list of all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n{'='*50}")
        print(f"DISPLAYING ALL DATA FROM DATABASE")
        print(f"{'='*50}\n")
        
        for table in tables:
            table_name = table[0]
            
            # Skip sqlite_sequence table if it exists (used for autoincrement)
            if table_name == 'sqlite_sequence':
                continue  
                
            print(f"\nTABLE: {table_name.upper()}")
            print("-" * (len(table_name) + 7))
            
            # Get all data from the current table
            cursor.execute(f"SELECT * FROM {table_name};")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Display the data in a nice table format
            if rows:
                print(tabulate(rows, headers=columns, tablefmt="grid"))
            else:
                print("No data found in this table")
                
    except sqlite3.Error as e:
        print(f"Error reading database: {e}")
    finally:
        conn.close()


def delete_all():
    """Delete all records from the users table"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Delete all users
        cursor.execute('DELETE FROM users')
        
        # Reset auto-increment counter (if using INTEGER PRIMARY KEY AUTOINCREMENT)
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="users"')
        
        conn.commit()
        print("Successfully deleted all users")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


    """Completely reset the users table"""
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # Drop the table
        cursor.execute('DROP TABLE IF EXISTS users')
        
        # Recreate the table with original schema
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT CHECK(role IN ('manager', 'employee')) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        print("Database reset complete")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    display_all_data()

