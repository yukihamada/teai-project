@app.route('/api/servers', methods=['GET'])
def get_servers():
    """サーバー一覧を取得（モックデータ）"""
    # 認証トークンを確認
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"success": False, "message": "Authorization token required"}), 401

    # トークンからユーザーIDを取得
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT user_id FROM sessions WHERE token = ?', (token,))
    session = cursor.fetchone()
    
    if not session:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 401
    
    user_id = session[0]
    
    # ユーザーが管理者かどうか確認
    cursor.execute('SELECT is_admin FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user or not user[0]:
        return jsonify({"success": False, "message": "Unauthorized access"}), 403
    
    # モックデータを返す
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
            }
        },
        {
            "ID": "i-0123456789abcdef1",
            "IP": "13.231.179.25",
            "State": "running",
            "Type": "t3a.large",
            "LaunchTime": "2025-03-26T12:15:00Z",
            "Status": "Running",
            "Memory": {
                "Total": "7982",
                "Used": "2876",
                "Free": "5106"
            }
        },
        {
            "ID": "i-0123456789abcdef2",
            "IP": "18.182.45.132",
            "State": "running",
            "Type": "t3a.xlarge",
            "LaunchTime": "2025-03-26T10:45:00Z",
            "Status": "Running",
            "Memory": {
                "Total": "15964",
                "Used": "5432",
                "Free": "10532"
            }
        },
        {
            "ID": "i-0123456789abcdef3",
            "IP": "35.74.12.87",
            "State": "stopped",
            "Type": "t3a.large",
            "LaunchTime": "2025-03-25T14:20:00Z",
            "Status": "Error",
            "Memory": None
        },
        {
            "ID": "i-0123456789abcdef4",
            "IP": None,
            "State": "pending",
            "Type": "t3a.large",
            "LaunchTime": "2025-03-26T13:55:00Z",
            "Status": "No IP",
            "Memory": None
        }
    ]
    
    return jsonify({"success": True, "servers": servers}), 200