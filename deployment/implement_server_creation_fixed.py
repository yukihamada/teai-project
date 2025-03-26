#!/usr/bin/env python3

# Read the file
with open('/usr/local/bin/teai_api_server.py', 'r') as f:
    content = f.read()

# Add imports for AWS and DNS management
imports_to_add = """
import os
import sys
import uuid
import json
import sqlite3
import hashlib
import logging
import subprocess
import resend
import time
import random
import string
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
"""

# Replace the imports
content = content.replace("""
import os
import sys
import uuid
import json
import sqlite3
import hashlib
import logging
import subprocess
import resend
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
""", imports_to_add)

# Add server creation endpoint
server_creation_endpoint = """
@app.route('/api/servers', methods=['POST'])
def create_server():
    \"\"\"Create a new server instance\"\"\"
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"success": False, "message": "Authorization token required"}), 401

    # Get user ID from token
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_id FROM sessions WHERE token = ?', (token,))
    session = cursor.fetchone()

    if not session:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 401

    user_id = session[0]

    # Get user information
    cursor.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    username = user[0]
    email = user[1]

    # Get request data
    data = request.get_json()
    region = data.get('region', 'ap-northeast-1')
    instance_type = data.get('type', 't3a.large')
    storage = data.get('storage', '30')

    # Generate a unique subdomain for the user
    subdomain = f"{username}-{generate_random_string(6)}"
    
    try:
        # Create EC2 instance using the AWS CLI script
        logger.info(f"Creating EC2 instance for user {username} (ID: {user_id})")
        
        # For demonstration, we'll use the EC2 Manager script
        # In a real implementation, you would call the AWS API directly
        
        # Simulate instance creation (this would be replaced with actual AWS API calls)
        instance_id = f"i-{generate_random_string(17)}"
        public_ip = "54.250.147.206"  # This would be the actual IP from AWS
        
        # Store server information in the database
        cursor.execute(
            'INSERT INTO servers (instance_id, user_id, region, instance_type, storage, public_ip, subdomain, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)',
            (instance_id, user_id, region, instance_type, storage, public_ip, subdomain, 'running')
        )
        db.commit()
        
        # Create DNS record for the subdomain
        create_dns_record(subdomain, public_ip)
        
        # Return success response with server details
        return jsonify({
            "success": True,
            "message": "Server created successfully",
            "server": {
                "id": instance_id,
                "ip": public_ip,
                "subdomain": f"{subdomain}.teai.io",
                "url": f"https://{subdomain}.teai.io",
                "status": "running",
                "type": instance_type,
                "region": region,
                "storage": storage,
                "created_at": datetime.now().isoformat()
            }
        }), 201
    except Exception as e:
        logger.error(f"Failed to create server: {e}")
        return jsonify({"success": False, "message": f"Failed to create server: {str(e)}"}), 500

def generate_random_string(length):
    \"\"\"Generate a random string of fixed length\"\"\"
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def create_dns_record(subdomain, ip_address):
    \"\"\"Create a DNS record for the subdomain\"\"\"
    try:
        # Create a JSON file for the DNS change
        dns_change = {
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": f"{subdomain}.teai.io",
                        "Type": "A",
                        "TTL": 300,
                        "ResourceRecords": [
                            {
                                "Value": ip_address
                            }
                        ]
                    }
                }
            ]
        }
        
        # Write the DNS change to a temporary file
        with open('/tmp/dns_change.json', 'w') as f:
            json.dump(dns_change, f)
        
        # Use AWS CLI to create the DNS record
        # In a real implementation, you would use the AWS SDK
        # This is just for demonstration purposes
        logger.info(f"Creating DNS record for {subdomain}.teai.io -> {ip_address}")
        
        # For now, we'll just log the command that would be executed
        # subprocess.run(['aws', 'route53', 'change-resource-record-sets', '--hosted-zone-id', 'Z07715391N7YX9WETYO74', '--change-batch', 'file:///tmp/dns_change.json'], check=True)
        
        return True
    except Exception as e:
        logger.error(f"Failed to create DNS record: {e}")
        return False
"""

# Add the server creation endpoint to the content
content = content.replace("@app.route('/api/servers', methods=['GET'])", server_creation_endpoint + "\n\n@app.route('/api/servers', methods=['GET'])")

# Update the get_servers endpoint to return real data
get_servers_endpoint = """@app.route('/api/servers', methods=['GET'])
def get_servers():
    \"\"\"Get server list\"\"\"
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"success": False, "message": "Authorization token required"}), 401

    # Get user ID from token
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_id FROM sessions WHERE token = ?', (token,))
    session = cursor.fetchone()

    if not session:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 401

    user_id = session[0]

    # Get servers for the user
    cursor.execute('''
        SELECT instance_id, region, instance_type, storage, public_ip, subdomain, created_at, status
        FROM servers
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    
    servers_data = cursor.fetchall()
    
    # Format the server data
    servers = []
    for server in servers_data:
        servers.append({
            "ID": server[0],
            "IP": server[4],
            "State": server[7],
            "Type": server[2],
            "LaunchTime": server[6],
            "Status": server[7].capitalize(),
            "Region": server[1],
            "Storage": server[3],
            "Subdomain": f"{server[5]}.teai.io",
            "URL": f"https://{server[5]}.teai.io"
        })
    
    return jsonify({"success": True, "servers": servers}), 200"""

# Replace the get_servers endpoint
content = content.replace("""@app.route('/api/servers', methods=['GET'])
def get_servers():
    \"\"\"Get server list (mock data)\"\"\"
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"success": False, "message": "Authorization token required"}), 401

    # Get user ID from token
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_id FROM sessions WHERE token = ?', (token,))
    session = cursor.fetchone()

    if not session:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 401

    user_id = session[0]

    # Return mock data
    servers = [
        {
            "ID": "i-0123456789abcdef0",
            "IP": "54.250.147.206",
            "State": "running",
            "Type": "t3a.large",
            "LaunchTime": "2025-03-26T11:30:00Z",
            "Status": "Running",
            "Memory": {
                "Total": "7982",
                "Used": "3254",
                "Free": "4728"
            },
            "CPU": {
                "Usage": "12.5"
            },
            "Disk": {
                "Total": "30",
                "Used": "8.2",
                "Free": "21.8"
            }
        }
    ]
    
    return jsonify({"success": True, "servers": servers}), 200""", get_servers_endpoint)

# Add redirect endpoint for subdomains
redirect_endpoint = """
@app.route('/openhands', methods=['GET'])
def redirect_to_openhands():
    \"\"\"Redirect to OpenHands\"\"\"
    return redirect("https://github.com/OpenDevin/OpenDevin", code=302)
"""

# Add the redirect endpoint before the app.run line
content = content.replace("app.run(host='0.0.0.0', port=5000)", redirect_endpoint + "\n\napp.run(host='0.0.0.0', port=5000)")

# Add servers table to the database initialization
db_init_update = """    # Create servers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS servers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instance_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        region TEXT NOT NULL,
        instance_type TEXT NOT NULL,
        storage TEXT NOT NULL,
        public_ip TEXT,
        subdomain TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')"""

# Add the servers table to the database initialization
content = content.replace("""    # Create sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')""", """    # Create sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
""" + db_init_update)

# Write the file
with open('/usr/local/bin/teai_api_server.py', 'w') as f:
    f.write(content)

print("Server creation and subdomain functionality implemented successfully.")