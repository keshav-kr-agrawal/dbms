# Lead Management System (LMS) - DBMS Mini Project

A clean, responsive, and fully functional **Lead Management System (LMS)** designed as a class-level DBMS project. It implements a Python Flask web interface on the front-end with dual database support on the back-end (**SQLite** for instant zero-configuration running, and **MySQL** for final database evaluations/submissions).

---

## 🛠️ Features Implemented
1. **Lead Capture & CRUD**: Create, read, update, and delete prospective clients.
2. **Lead Assignment**: Admins/Managers can assign or reassign leads to sales representatives.
3. **Follow-Up Scheduling**: Schedule and mark follow-ups (calls, demo meetings, emails) as completed.
4. **Customer Conversion**: Mark a qualified lead as a converted customer and log company details and transaction revenue.
5. **Database Trigger (Audit Trail)**: An database-level trigger (`after_lead_insert`) automatically populates the `activity_log` table whenever a new lead is inserted.
6. **Stored Procedure (Analytics)**: Calls a database-level procedure (`GetLeadSummaryByRep`) to retrieve summaries (total leads, open leads, converted leads) for a representative.
7. **Role-Based Permissions**: Simulate different roles (Administrator, Sales Manager, Sales Representative) directly from the UI.

---

## 📂 Project Structure
* `app.py`: Main Flask server and APIs.
* `database.py`: Database connection helpers, schema generation, mock data loaders, and stored procedure wrappers.
* `config.py`: Configuration toggle (`DB_TYPE = 'sqlite'` or `'mysql'`) and MySQL login configuration.
* `schema_sqlite.sql` / `schema_mysql.sql`: SQL DDL files defining tables, relationships (foreign keys), triggers, and procedures.
* `templates/index.html`: Fully responsive HTML & JavaScript Single Page App dashboard.
* `static/css/style.css`: Modern styling sheet using a dark, neon glassmorphism aesthetic.

---

## 🚀 Setup & Execution

### 1. Install Dependencies
You only need to install **Flask** (and `mysql-connector-python` if using MySQL):
```bash
pip install Flask mysql-connector-python
```

### 2. Run the Server
By default, the project runs on **SQLite** (a local database file `lms.db` is automatically created and filled with tailormade mock data). Run:
```bash
python app.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 🔌 Switching to MySQL (For Submission/Grading)
If your professor requires you to run using a real MySQL instance:
1. Ensure your local MySQL server is running.
2. Open [config.py](file:///Users/keshav/dbms/config.py) and change `DB_TYPE` to `'mysql'`:
   ```python
   DB_TYPE = 'mysql'
   ```
3. Update `MYSQL_CONFIG` in `config.py` with your username, password, port, etc.:
   ```python
   MYSQL_CONFIG = {
       'host': 'localhost',
       'user': 'root',
       'password': 'YOUR_PASSWORD_HERE',
       'database': 'lead_management',
       'port': 3306
   }
   ```
4. Run `python app.py`. The application will automatically connect, create the `lead_management` database, build all tables, insert mock data, configure the trigger, and register the stored procedure!

---

## 📝 Key DBMS Concepts Explained (For Lab Viva)

### 1. Database Schema
Our database comprises 6 connected tables:
* `departments`: Department meta-data.
* `sales_representatives`: Group members & employees (linked to `departments` via 1:N foreign key).
* `leads`: Potential customers (linked to `sales_representatives` via 1:N foreign key).
* `customers`: Converted leads (linked to `leads` via a strict 1:1 foreign key relation).
* `follow_ups`: Scheduled events (linked to `leads` and `sales_representatives`).
* `activity_log`: Detailed action history.

### 2. Stored Procedure: `GetLeadSummaryByRep`
Used to run analytics on representative performances by calculating total, open, and converted leads:
```sql
CREATE PROCEDURE GetLeadSummaryByRep(IN repID INT)
BEGIN
    SELECT 
        repID AS rep_id,
        COUNT(*) AS total_leads,
        SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_leads,
        SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS converted_leads
    FROM leads 
    WHERE assigned_to = repID;
END;
```

### 3. Database Trigger: `after_lead_insert`
Fires automatically after any `INSERT` query on the `leads` table to log actions into the `activity_log` audit table:
```sql
CREATE TRIGGER after_lead_insert
AFTER INSERT ON leads FOR EACH ROW
BEGIN
    INSERT INTO activity_log(lead_id, rep_id, action, action_date, description)
    VALUES (NEW.lead_id, NEW.assigned_to, 'Lead Created', NOW(), 'New lead added.');
END;
```
