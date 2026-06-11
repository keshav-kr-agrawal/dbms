-- MySQL Schema for Lead Management System
-- Use this file to import the database structure into MySQL

CREATE DATABASE IF NOT EXISTS lead_management;
USE lead_management;

-- 1. Departments Table
CREATE TABLE IF NOT EXISTS departments (
    dept_id INT PRIMARY KEY AUTO_INCREMENT,
    dept_name VARCHAR(100) NOT NULL,
    dept_head VARCHAR(100),
    location VARCHAR(100)
);

-- 2. Sales Representatives Table
CREATE TABLE IF NOT EXISTS sales_representatives (
    rep_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    designation VARCHAR(50),
    dept_id INT,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id) ON DELETE SET NULL
);

-- 3. Leads Table
CREATE TABLE IF NOT EXISTS leads (
    lead_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    source VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Open', -- e.g. Open, Contacted, Converted, Lost
    assigned_to INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (assigned_to) REFERENCES sales_representatives(rep_id) ON DELETE SET NULL
);

-- 4. Customers Table (1:1 Relationship with Lead)
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    lead_id INT UNIQUE NOT NULL,
    company_name VARCHAR(100),
    address VARCHAR(255),
    conversion_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_value DECIMAL(10, 2) DEFAULT 0.00,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE
);

-- 5. Follow-ups Table
CREATE TABLE IF NOT EXISTS follow_ups (
    followup_id INT PRIMARY KEY AUTO_INCREMENT,
    lead_id INT NOT NULL,
    rep_id INT,
    followup_date DATETIME NOT NULL,
    remarks TEXT,
    next_followup_date DATETIME,
    status VARCHAR(50) DEFAULT 'Scheduled', -- e.g. Scheduled, Completed, Missed
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE CASCADE,
    FOREIGN KEY (rep_id) REFERENCES sales_representatives(rep_id) ON DELETE SET NULL
);

-- 6. Activity Log Table
CREATE TABLE IF NOT EXISTS activity_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    lead_id INT,
    rep_id INT,
    action VARCHAR(100) NOT NULL,
    action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id) ON DELETE SET NULL,
    FOREIGN KEY (rep_id) REFERENCES sales_representatives(rep_id) ON DELETE SET NULL
);

-- 8.2 Stored Procedure (Retrieves summary of leads assigned to a specific representative)
DELIMITER //
DROP PROCEDURE IF EXISTS GetLeadSummaryByRep //
CREATE PROCEDURE GetLeadSummaryByRep(IN repID INT)
BEGIN
    SELECT 
        repID AS rep_id,
        COUNT(*) AS total_leads,
        SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_leads,
        SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) AS converted_leads
    FROM leads 
    WHERE assigned_to = repID;
END //
DELIMITER ;

-- 8.3 Trigger (Automatically logs lead creation)
DELIMITER //
DROP TRIGGER IF EXISTS after_lead_insert //
CREATE TRIGGER after_lead_insert
AFTER INSERT ON leads FOR EACH ROW
BEGIN
    INSERT INTO activity_log(lead_id, rep_id, action, action_date, description)
    VALUES (NEW.lead_id, NEW.assigned_to, 'Lead Created', NOW(), 'New lead added.');
END //
DELIMITER ;
