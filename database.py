import sqlite3
import os
import config

try:
    import mysql.connector
except ImportError:
    mysql = None

def get_connection():
    """Returns a database connection based on DB_TYPE in config.py."""
    if config.DB_TYPE == 'sqlite':
        conn = sqlite3.connect(config.SQLITE_DB_PATH)
        # Enable foreign key support in SQLite
        conn.execute("PRAGMA foreign_keys = ON;")
        # Return rows as dictionaries
        conn.row_factory = sqlite3.Row
        return conn
    elif config.DB_TYPE == 'mysql':
        if mysql is None:
            raise ImportError(
                "mysql-connector-python is not installed. "
                "Please install it using: pip install mysql-connector-python"
            )
        # Establish MySQL connection
        conn = mysql.connector.connect(
            host=config.MYSQL_CONFIG['host'],
            user=config.MYSQL_CONFIG['user'],
            password=config.MYSQL_CONFIG['password'],
            port=config.MYSQL_CONFIG['port']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.MYSQL_CONFIG['database']}")
        conn.database = config.MYSQL_CONFIG['database']
        cursor.close()
        return conn
    else:
        raise ValueError(f"Unknown DB_TYPE: {config.DB_TYPE}")

def execute_query(query, params=(), fetch='none'):
    """Helper function to execute SQL queries."""
    conn = get_connection()
    try:
        if config.DB_TYPE == 'sqlite':
            cursor = conn.cursor()
            cursor.execute(query, params)
            if fetch == 'all':
                # Convert SQLite rows to list of dicts
                result = [dict(row) for row in cursor.fetchall()]
            elif fetch == 'one':
                row = cursor.fetchone()
                result = dict(row) if row else None
            else:
                conn.commit()
                result = cursor.lastrowid
            cursor.close()
        else: # MySQL
            # dictionary=True returns rows as dicts
            cursor = conn.cursor(dictionary=True)
            # Replace ? with %s for MySQL queries if we use standard queries
            if '?' in query:
                query = query.replace('?', '%s')
            cursor.execute(query, params)
            if fetch == 'all':
                result = cursor.fetchall()
            elif fetch == 'one':
                result = cursor.fetchone()
            else:
                conn.commit()
                result = cursor.lastrowid
            cursor.close()
        return result
    finally:
        conn.close()

def init_db():
    """Initializes the database schema and loads mock data if empty."""
    if config.DB_TYPE == 'sqlite':
        db_exists = os.path.exists(config.SQLITE_DB_PATH)
        conn = get_connection()
        try:
            # If database table check fails, we build it
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads';")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_sqlite.sql')
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                conn.executescript(schema_sql)
                conn.commit()
                print("SQLite database schema initialized successfully.")
                
                # Check if data already exists, if not, populate it
                cursor.execute("SELECT COUNT(*) FROM departments;")
                if cursor.fetchone()[0] == 0:
                    populate_mock_data(conn)
            cursor.close()
        finally:
            conn.close()
    elif config.DB_TYPE == 'mysql':
        conn = get_connection()
        try:
            cursor = conn.cursor()
            # Check if tables exist
            cursor.execute("SHOW TABLES LIKE 'leads';")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema_mysql.sql')
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                # Execute MySQL schema
                # Since schema_mysql.sql contains DELIMITER and multiple statements, 
                # we split it and execute statements. To keep it simple, we execute statements individually.
                # Remove DELIMITER and replace lines
                statements = []
                current_stmt = []
                in_procedure = False
                
                for line in schema_sql.split('\n'):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('--'):
                        continue
                    if 'DELIMITER' in stripped:
                        continue
                    current_stmt.append(line)
                    if stripped.endswith(';') and not in_procedure:
                        statements.append(' '.join(current_stmt))
                        current_stmt = []
                    elif 'BEGIN' in stripped:
                        in_procedure = True
                    elif 'END' in stripped:
                        in_procedure = False
                        statements.append(' '.join(current_stmt))
                        current_stmt = []
                
                for stmt in statements:
                    if stmt.strip():
                        try:
                            cursor.execute(stmt)
                        except Exception as e:
                            print(f"Error executing statement: {stmt}\nError: {e}")
                
                conn.commit()
                print("MySQL database schema initialized successfully.")
                populate_mock_data(conn)
            cursor.close()
        finally:
            conn.close()

def populate_mock_data(conn):
    """Populates the database with initial mock data representing student groups and sample leads."""
    cursor = conn.cursor()
    
    # 1. Insert Departments
    depts = [
        (1, 'Sales & Marketing', 'Prof. PRATHIMA M G', 'Block A, 3rd Floor'),
        (2, 'Enterprise Sales', 'Prof. MANJUSHREE N S', 'Block A, 4th Floor'),
        (3, 'Customer Success', 'Dr. Ramesh Kumar', 'Block B, 2nd Floor')
    ]
    placeholder = '?' if config.DB_TYPE == 'sqlite' else '%s'
    cursor.executemany(
        f"INSERT INTO departments (dept_id, dept_name, dept_head, location) VALUES ({placeholder},{placeholder},{placeholder},{placeholder})",
        depts
    )
    
    # 2. Insert Sales Representatives (Student names from the PDF!)
    reps = [
        (1, 'Harshiya Mahajan', 'harshiyamahajan2006@gmail.com', '7006637508', 'Sales Exec', 1),
        (2, 'Ishaan Gupta', 'ishaangupta011205@gmail.com', '9670333459', 'Sales Manager', 2),
        (3, 'Keshav Kr Agrawal', 'agrawalkeshav002@gmail.com', '9263225604', 'VP of Sales', 2)
    ]
    cursor.executemany(
        f"INSERT INTO sales_representatives (rep_id, name, email, phone, designation, dept_id) VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder})",
        reps
    )
    
    # 3. Insert Leads (Trigger will automatically log these in SQLite/MySQL!)
    leads = [
        (1, 'Amit', 'Sharma', 'amit.sharma@example.com', '9876543210', 'Website', 'Open', 1),
        (2, 'Priya', 'Patel', 'priya.patel@example.com', '9812345678', 'Social Media', 'Contacted', 1),
        (3, 'Rajesh', 'Verma', 'rajesh.verma@example.com', '9988776655', 'Email Campaign', 'Converted', 2),
        (4, 'Sneha', 'Reddy', 'sneha.reddy@example.com', '9765432109', 'Walk-in', 'Open', 3),
        (5, 'Vikram', 'Singh', 'vikram.singh@example.com', '9555123456', 'Website', 'Lost', 2)
    ]
    cursor.executemany(
        f"INSERT INTO leads (lead_id, first_name, last_name, email, phone, source, status, assigned_to) VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder})",
        leads
    )
    
    # 4. Insert Converted Customers
    customers = [
        (1, 3, 'Verma Tech Solutions', '123, MG Road, Bengaluru', 250000.00)
    ]
    cursor.executemany(
        f"INSERT INTO customers (customer_id, lead_id, company_name, address, total_value) VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder})",
        customers
    )
    
    # 5. Insert Follow-ups
    followups = [
        (1, 1, 1, '2026-06-15 10:00:00', 'Initial intro call scheduled', '2026-06-15 10:30:00', 'Scheduled'),
        (2, 2, 1, '2026-06-10 14:00:00', 'Discussed requirements, customer was interested', '2026-06-14 11:00:00', 'Completed'),
        (3, 4, 3, '2026-06-12 16:30:00', 'Demo scheduled for enterprise platform', '2026-06-12 17:30:00', 'Scheduled')
    ]
    cursor.executemany(
        f"INSERT INTO follow_ups (followup_id, lead_id, rep_id, followup_date, remarks, next_followup_date, status) VALUES ({placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder},{placeholder})",
        followups
    )
    
    # For activity log, MySQL/SQLite triggers will run on INSERT of leads.
    # But for departments and reps, we can log them manually if we want,
    # or just rely on the trigger. Since the trigger logs 'Lead Created',
    # those leads we inserted will have corresponding logs. Let's make sure
    # they are committed.
    conn.commit()
    print("Mock data loaded successfully.")

def get_lead_summary_by_rep(rep_id):
    """Simulates/calls the GetLeadSummaryByRep stored procedure."""
    if config.DB_TYPE == 'mysql':
        conn = get_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.callproc('GetLeadSummaryByRep', [rep_id])
            # callproc returns results via stored results in mysql connector
            results = []
            for result in cursor.stored_results():
                results.extend(result.fetchall())
            cursor.close()
            return results[0] if results else {
                'rep_id': rep_id, 'total_leads': 0, 'open_leads': 0, 'converted_leads': 0
            }
        finally:
            conn.close()
    else:
        # SQLite simulation of the stored procedure query
        query = """
        SELECT 
            ? AS rep_id,
            COUNT(*) AS total_leads,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_leads,
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS converted_leads
        FROM leads 
        WHERE assigned_to = ?;
        """
        result = execute_query(query, (rep_id, rep_id), fetch='one')
        if not result or result['total_leads'] == 0:
            return {'rep_id': rep_id, 'total_leads': 0, 'open_leads': 0, 'converted_leads': 0}
        return result
