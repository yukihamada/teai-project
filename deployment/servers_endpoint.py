@app.route('/api/servers', methods=['GET'])
def get_servers():
    """サーバー一覧を取得"""
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
    
    # EC2インスタンスの情報を取得
    try:
        # AWS CLIを使用してEC2インスタンスの情報を取得
        result = subprocess.run(
            ['aws', 'ec2', 'describe-instances', 
             '--filters', 'Name=tag:Name,Values=OpenHands', 
             '--query', 'Reservations[*].Instances[*].{ID:InstanceId,IP:PublicIpAddress,State:State.Name,Type:InstanceType,LaunchTime:LaunchTime}',
             '--output', 'json',
             '--region', 'ap-northeast-1'],
            capture_output=True, text=True, check=True
        )
        
        servers = json.loads(result.stdout)
        # フラット化
        servers = [item for sublist in servers for item in sublist]
        
        # 各サーバーのステータスを取得
        for server in servers:
            if server.get('IP'):
                try:
                    # SSHで接続してステータスを取得
                    ssh_result = subprocess.run(
                        ['ssh', '-i', '/home/ec2-user/.ssh/openhands-key.pem', 
                         '-o', 'StrictHostKeyChecking=no', 
                         '-o', 'ConnectTimeout=5',
                         f'ec2-user@{server["IP"]}', 
                         'systemctl status openhands-app --no-pager'],
                        capture_output=True, text=True, timeout=10
                    )
                    
                    if ssh_result.returncode == 0:
                        server['Status'] = 'Running'
                    else:
                        server['Status'] = 'Error'
                        
                    # メモリ使用量を取得
                    mem_result = subprocess.run(
                        ['ssh', '-i', '/home/ec2-user/.ssh/openhands-key.pem', 
                         '-o', 'StrictHostKeyChecking=no', 
                         '-o', 'ConnectTimeout=5',
                         f'ec2-user@{server["IP"]}', 
                         'free -m | grep Mem'],
                        capture_output=True, text=True, timeout=5
                    )
                    
                    if mem_result.returncode == 0:
                        mem_info = mem_result.stdout.strip().split()
                        server['Memory'] = {
                            'Total': mem_info[1],
                            'Used': mem_info[2],
                            'Free': mem_info[3]
                        }
                    
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    server['Status'] = 'Unreachable'
            else:
                server['Status'] = 'No IP'
        
        return jsonify({"success": True, "servers": servers}), 200
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting servers: {e}")
        return jsonify({"success": False, "message": "Failed to get servers", "error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({"success": False, "message": "An unexpected error occurred", "error": str(e)}), 500