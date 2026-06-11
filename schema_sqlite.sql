-- SQLite Schema for Lead Management System
-- Used for fast, local, zero-config testing

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_name TEXT NOT NULL,
    dept_head TEXT,
    location TEXT
);

-- 2. Sales Representatives Table
CREATE TABLE IF NOT EXISTS sales_representatives (
    rep_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    designation TEXT,
    dept_id INTEGER,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL
);

-- 3. Leads Table
CREATE TABLE IF NOT EXISTS leads (
    lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    source TEXT,
    status TEXT DEFAULT 'Open', -- e.g. Open, Contacted, Converted, Lost
    assigned_to INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES sales_representatives(rep_id) ON DELETE SET NULL
);

-- 4. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER UNIQUE NOT NULL,
    company_name TEXT,
    address TEXT,
    conversion_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_value REAL DEFAULT 0.00,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE
);

-- 5. Follow-ups Table
CREATE TABLE IF NOT EXISTS follow_ups (
    followup_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL,
    rep_id INTEGER,
    followup_date DATETIME NOT NULL,
    remarks TEXT,
    next_followup_date DATETIME,
    status TEXT DEFAULT 'Scheduled', -- e.g. Scheduled, Completed, Missed
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE,
    FOREIGN KEY (rep_id) REFERENCES sales_representatives(rep_id) ON DELETE SET NULL
);

-- 6. Activity Log Table
CREATE TABLE IF NOT EXISTS activity_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    rep_id INTEGER,
    action TEXT NOT NULL,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE SET NULL,
    FOREIGN KEY (rep_id) REFERENCES sales_representatives(rep_id) ON DELETE SET NULL
);

-- Trigger to automatically insert entry to activity_log on lead insert
DROP TRIGGER IF EXISTS after_lead_insert;
CREATE TRIGGER after_lead_insert
AFTER INSERT ON leads
BEGIN
    INSERT INTO activity_log(lead_id, rep_id, action, action_date, description)
    VALUES (NEW.lead_id, NEW.assigned_to, 'Lead Created', datetime('now', 'localtime'), 'New lead added.');
END;
