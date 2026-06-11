import os

# Configuration for Lead Management System (LMS)

# Database type: 'sqlite' or 'mysql'
DB_TYPE = 'sqlite'  # Change to 'mysql' to use MySQL

# SQLite Settings
SQLITE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lms.db')

# MySQL Settings
# Adjust these values to match your local MySQL configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Enter your MySQL password here
    'database': 'lead_management',
    'port': 3306
}
