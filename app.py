from flask import Flask, render_template, jsonify, request
import database
import config
from datetime import datetime

app = Flask(__name__)

# Initialize the database on startup
with app.app_context():
    database.init_db()

@app.route('/')
def index():
    return render_template('index.html')

# --- LEADS ENDPOINTS ---

@app.route('/api/leads', methods=['GET'])
def get_leads():
    query = """
        SELECT l.*, r.name AS rep_name, d.dept_name
        FROM leads l
        LEFT JOIN sales_representatives r ON l.assigned_to = r.rep_id
        LEFT JOIN departments d ON r.dept_id = d.dept_id
        ORDER BY l.created_at DESC
    """
    try:
        leads = database.execute_query(query, fetch='all')
        return jsonify(leads)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads', methods=['POST'])
def add_lead():
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone = data.get('phone')
    source = data.get('source')
    assigned_to = data.get('assigned_to') # rep_id or None

    if not first_name or not last_name:
        return jsonify({"error": "First Name and Last Name are required."}), 400

    query = """
        INSERT INTO leads (first_name, last_name, email, phone, source, status, assigned_to, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'Open', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """
    params = (first_name, last_name, email, phone, source, assigned_to if assigned_to else None)

    try:
        lead_id = database.execute_query(query, params)
        return jsonify({"message": "Lead created successfully", "lead_id": lead_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    query = "SELECT * FROM leads WHERE lead_id = ?"
    try:
        lead = database.execute_query(query, (lead_id,), fetch='one')
        if not lead:
            return jsonify({"error": "Lead not found"}), 404
        return jsonify(lead)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['PUT'])
def update_lead(lead_id):
    data = request.json
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone = data.get('phone')
    source = data.get('source')
    status = data.get('status')
    assigned_to = data.get('assigned_to')

    if not first_name or not last_name:
        return jsonify({"error": "First Name and Last Name are required."}), 400

    # Get current status to see if it changed for logging
    old_lead = database.execute_query("SELECT status, assigned_to FROM leads WHERE lead_id = ?", (lead_id,), fetch='one')
    if not old_lead:
        return jsonify({"error": "Lead not found"}), 404

    query = """
        UPDATE leads 
        SET first_name = ?, last_name = ?, email = ?, phone = ?, source = ?, status = ?, assigned_to = ?, updated_at = CURRENT_TIMESTAMP
        WHERE lead_id = ?
    """
    params = (first_name, last_name, email, phone, source, status, assigned_to if assigned_to else None, lead_id)

    try:
        database.execute_query(query, params)
        
        # Log manual changes to activity log
        log_entries = []
        if old_lead['status'] != status:
            log_entries.append(("Status Updated", f"Status changed from '{old_lead['status']}' to '{status}'."))
        if old_lead['assigned_to'] != assigned_to:
            rep_name = "None"
            if assigned_to:
                rep = database.execute_query("SELECT name FROM sales_representatives WHERE rep_id = ?", (assigned_to,), fetch='one')
                if rep:
                    rep_name = rep['name']
            log_entries.append(("Lead Reassigned", f"Lead reassigned to representative: {rep_name}."))

        for action, desc in log_entries:
            log_query = """
                INSERT INTO activity_log (lead_id, rep_id, action, action_date, description)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
            """
            database.execute_query(log_query, (lead_id, assigned_to if assigned_to else None, action, desc))

        return jsonify({"message": "Lead updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    query = "DELETE FROM leads WHERE lead_id = ?"
    try:
        # Before deleting, insert a log or just delete (cascade deletes customer and followups)
        database.execute_query(query, (lead_id,))
        return jsonify({"message": "Lead deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- SALES REPRESENTATIVES & DEPARTMENTS ENDPOINTS ---

@app.route('/api/reps', methods=['GET'])
def get_reps():
    query = """
        SELECT r.*, d.dept_name, d.location
        FROM sales_representatives r
        LEFT JOIN departments d ON r.dept_id = d.dept_id
        ORDER BY r.name ASC
    """
    try:
        reps = database.execute_query(query, fetch='all')
        return jsonify(reps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/departments', methods=['GET'])
def get_departments():
    query = "SELECT * FROM departments ORDER BY dept_name ASC"
    try:
        depts = database.execute_query(query, fetch='all')
        return jsonify(depts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- LEAD ASSIGNMENT ENDPOINT ---

@app.route('/api/assignments', methods=['POST'])
def assign_lead():
    data = request.json
    lead_id = data.get('lead_id')
    rep_id = data.get('rep_id')

    if not lead_id:
        return jsonify({"error": "Lead ID is required."}), 400

    try:
        # Get representative name for log
        rep_name = "Unassigned"
        if rep_id:
            rep = database.execute_query("SELECT name FROM sales_representatives WHERE rep_id = ?", (rep_id,), fetch='one')
            if rep:
                rep_name = rep['name']
        
        # Update Lead
        database.execute_query("UPDATE leads SET assigned_to = ?, updated_at = CURRENT_TIMESTAMP WHERE lead_id = ?", (rep_id if rep_id else None, lead_id))
        
        # Log to Activity Log
        log_query = """
            INSERT INTO activity_log (lead_id, rep_id, action, action_date, description)
            VALUES (?, ?, 'Lead Assigned', CURRENT_TIMESTAMP, ?)
        """
        database.execute_query(log_query, (lead_id, rep_id if rep_id else None, f"Lead assigned to {rep_name}."))

        return jsonify({"message": f"Lead successfully assigned to {rep_name}."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- FOLLOW-UPS ENDPOINTS ---

@app.route('/api/followups', methods=['GET'])
def get_followups():
    query = """
        SELECT f.*, l.first_name, l.last_name, r.name AS rep_name
        FROM follow_ups f
        INNER JOIN leads l ON f.lead_id = l.lead_id
        LEFT JOIN sales_representatives r ON f.rep_id = r.rep_id
        ORDER BY f.followup_date DESC
    """
    try:
        followups = database.execute_query(query, fetch='all')
        return jsonify(followups)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/followups', methods=['POST'])
def add_followup():
    data = request.json
    lead_id = data.get('lead_id')
    rep_id = data.get('rep_id')
    followup_date = data.get('followup_date')
    remarks = data.get('remarks')
    next_followup_date = data.get('next_followup_date')

    if not lead_id or not followup_date:
        return jsonify({"error": "Lead ID and Follow-up Date are required."}), 400

    query = """
        INSERT INTO follow_ups (lead_id, rep_id, followup_date, remarks, next_followup_date, status)
        VALUES (?, ?, ?, ?, ?, 'Scheduled')
    """
    params = (lead_id, rep_id if rep_id else None, followup_date, remarks, next_followup_date if next_followup_date else None)

    try:
        followup_id = database.execute_query(query, params)
        
        # Log to Activity Log
        log_query = """
            INSERT INTO activity_log (lead_id, rep_id, action, action_date, description)
            VALUES (?, ?, 'Follow-up Scheduled', CURRENT_TIMESTAMP, ?)
        """
        database.execute_query(log_query, (lead_id, rep_id if rep_id else None, f"New follow-up scheduled for {followup_date}."))
        
        return jsonify({"message": "Follow-up scheduled successfully", "followup_id": followup_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/followups/<int:followup_id>/complete', methods=['POST'])
def complete_followup(followup_id):
    data = request.json or {}
    remarks = data.get('remarks', 'Follow-up completed.')
    
    try:
        # Get followup details
        followup = database.execute_query("SELECT lead_id, rep_id FROM follow_ups WHERE followup_id = ?", (followup_id,), fetch='one')
        if not followup:
            return jsonify({"error": "Follow-up not found"}), 404

        # Update follow-up status
        database.execute_query("UPDATE follow_ups SET status = 'Completed', remarks = ? WHERE followup_id = ?", (remarks, followup_id))
        
        # Log to Activity Log
        log_query = """
            INSERT INTO activity_log (lead_id, rep_id, action, action_date, description)
            VALUES (?, ?, 'Follow-up Completed', CURRENT_TIMESTAMP, ?)
        """
        database.execute_query(log_query, (followup['lead_id'], followup['rep_id'], f"Follow-up marked completed. Remarks: {remarks}"))

        return jsonify({"message": "Follow-up marked as completed."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- CUSTOMER CONVERSION ENDPOINT ---

@app.route('/api/customers', methods=['GET'])
def get_customers():
    query = """
        SELECT c.*, l.first_name, l.last_name, l.email, l.phone, r.name AS rep_name
        FROM customers c
        INNER JOIN leads l ON c.lead_id = l.lead_id
        LEFT JOIN sales_representatives r ON l.assigned_to = r.rep_id
        ORDER BY c.conversion_date DESC
    """
    try:
        customers = database.execute_query(query, fetch='all')
        return jsonify(customers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/customers/convert', methods=['POST'])
def convert_lead():
    data = request.json
    lead_id = data.get('lead_id')
    company_name = data.get('company_name')
    address = data.get('address')
    total_value = data.get('total_value', 0.0)

    if not lead_id:
        return jsonify({"error": "Lead ID is required."}), 400

    try:
        # Check if already converted
        existing = database.execute_query("SELECT customer_id FROM customers WHERE lead_id = ?", (lead_id,), fetch='one')
        if existing:
            return jsonify({"error": "Lead is already converted to a customer."}), 400

        lead = database.execute_query("SELECT assigned_to, first_name, last_name FROM leads WHERE lead_id = ?", (lead_id,), fetch='one')
        if not lead:
            return jsonify({"error": "Lead not found."}), 404

        # 1. Insert Customer Record
        customer_query = """
            INSERT INTO customers (lead_id, company_name, address, conversion_date, total_value)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """
        customer_id = database.execute_query(customer_query, (lead_id, company_name, address, total_value))

        # 2. Update Lead Status
        database.execute_query("UPDATE leads SET status = 'Converted', updated_at = CURRENT_TIMESTAMP WHERE lead_id = ?", (lead_id,))

        # 3. Log to Activity Log
        log_query = """
            INSERT INTO activity_log (lead_id, rep_id, action, action_date, description)
            VALUES (?, ?, 'Lead Converted', CURRENT_TIMESTAMP, ?)
        """
        desc = f"Lead converted to Customer. Company: {company_name}. Deal Value: ₹{total_value}"
        database.execute_query(log_query, (lead_id, lead['assigned_to'], desc))

        return jsonify({"message": f"Lead {lead['first_name']} {lead['last_name']} successfully converted to Customer!", "customer_id": customer_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- ACTIVITY LOGS ENDPOINT ---

@app.route('/api/logs', methods=['GET'])
def get_logs():
    query = """
        SELECT al.*, l.first_name, l.last_name, r.name AS rep_name
        FROM activity_log al
        LEFT JOIN leads l ON al.lead_id = l.lead_id
        LEFT JOIN sales_representatives r ON al.rep_id = r.rep_id
        ORDER BY al.action_date DESC
        LIMIT 50
    """
    try:
        logs = database.execute_query(query, fetch='all')
        return jsonify(logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- ANALYTICS / STORED PROCEDURE ENDPOINTS ---

@app.route('/api/analytics/rep/<int:rep_id>', methods=['GET'])
def get_rep_summary(rep_id):
    try:
        # Retrieve stored procedure result
        summary = database.get_lead_summary_by_rep(rep_id)
        # Fetch representative name to add to details
        rep = database.execute_query("SELECT name FROM sales_representatives WHERE rep_id = ?", (rep_id,), fetch='one')
        summary['rep_name'] = rep['name'] if rep else 'Unknown'
        return jsonify(summary)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/overview', methods=['GET'])
def get_analytics_overview():
    try:
        stats = {}
        # 1. Total Leads
        stats['total_leads'] = database.execute_query("SELECT COUNT(*) AS count FROM leads", fetch='one')['count']
        
        # 2. Leads by Status
        status_data = database.execute_query("SELECT status, COUNT(*) AS count FROM leads GROUP BY status", fetch='all')
        stats['by_status'] = {row['status']: row['count'] for row in status_data}
        
        # 3. Leads by Source
        source_data = database.execute_query("SELECT source, COUNT(*) AS count FROM leads GROUP BY source", fetch='all')
        stats['by_source'] = {row['source'] or 'Unknown': row['count'] for row in source_data}
        
        # 4. Total Customers & Revenue
        revenue_data = database.execute_query("SELECT COUNT(*) AS total_customers, SUM(total_value) AS total_revenue FROM customers", fetch='one')
        stats['total_customers'] = revenue_data['total_customers']
        stats['total_revenue'] = revenue_data['total_revenue'] or 0.0
        
        # 5. Workload Distribution
        workload = database.execute_query("""
            SELECT r.name, COUNT(l.lead_id) AS lead_count
            FROM sales_representatives r
            LEFT JOIN leads l ON r.rep_id = l.assigned_to
            GROUP BY r.rep_id, r.name
        """, fetch='all')
        stats['workload'] = workload
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run server
    app.run(debug=True, host='0.0.0.0', port=5000)
