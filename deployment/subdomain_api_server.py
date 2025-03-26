#!/usr/bin/env python3
import json
import logging
import os
import hashlib
import time
import subprocess
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import sqlite3
import uuid
from datetime import datetime, timedelta

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/teai-api-server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("teai-api-server")

app = Flask(__name__)
CORS(app)

# データベース設定
DATABASE_PATH = '/var/lib/teai/teai.db'
NGINX_CONFIG_PATH = '/etc/nginx/conf.d/teai_instances.conf'
NGINX_MAP_TEMPLATE = """
# TeAI インスタンスマッピング - 自動生成されたファイルです
# 最終更新: {timestamp}

map $instance_id $backend_server {{
    default "127.0.0.1:3000";  # デフォルトサーバー
{instance_mappings}
}}
"""

def get_db():
    """データベース接続を取得"""
    db = getattr(g, '_database', None)
    if db is None:
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """アプリケーションコンテキスト終了時にDB接続を閉じる"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """データベースの初期化"""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # ユーザーテーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # インスタンステーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS instances (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            subdomain TEXT UNIQUE NOT NULL,
            ip_address TEXT NOT NULL,
            port INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # セッションテーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        db.commit()

def update_nginx_config():
    """Nginxの設定ファイルを更新"""
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT subdomain, ip_address, port FROM instances WHERE status = "active"')
        instances = cursor.fetchall()
        
        mappings = []
        for instance in instances:
            mappings.append(f'    {instance["subdomain"]} "{instance["ip_address"]}:{instance["port"]}";')
        
        instance_mappings = "\n".join(mappings)
        config_content = NGINX_MAP_TEMPLATE.format(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            instance_mappings=instance_mappings
        )
        
        with open(NGINX_CONFIG_PATH, 'w') as f:
            f.write(config_content)
        
        # Nginxの設定をリロード
        try:
            subprocess.run(['nginx', '-s', 'reload'], check=True)
            logger.info("Nginx configuration reloaded successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reload Nginx: {e}")

@app.route('/api/register', methods=['POST'])
def register():
    """新規ユーザー登録"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    # パスワードハッシュ化
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        user_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO users (id, username, email, password_hash) VALUES (?, ?, ?, ?)',
            (user_id, username, email, password_hash)
        )
        db.commit()
        return jsonify({"success": True, "message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username or email already exists"}), 409
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"success": False, "message": "Registration failed"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """ユーザーログイン"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not all([username, password]):
        return jsonify({"success": False, "message": "Missing username or password"}), 400
    
    # パスワードハッシュ化
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        'SELECT id, username, email FROM users WHERE username = ? AND password_hash = ?',
        (username, password_hash)
    )
    user = cursor.fetchone()
    
    if user:
        # セッショントークン生成
        token = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7)
        
        # 既存のセッションを削除
        cursor.execute('DELETE FROM sessions WHERE user_id = ?', (user['id'],))
        
        # 新しいセッションを作成
        session_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO sessions (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)',
            (session_id, user['id'], token, expires_at)
        )
        
        # 最終ログイン時間を更新
        cursor.execute(
            'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            (user['id'],)
        )
        
        db.commit()
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email']
            },
            "token": token,
            "expires_at": expires_at.isoformat()
        }), 200
    else:
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

@app.route('/auth', methods=['GET'])
def auth():
    """認証チェック"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({"authenticated": False, "message": "No token provided"}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute(
        '''
        SELECT s.user_id, u.username, u.email
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ? AND s.expires_at > CURRENT_TIMESTAMP
        ''',
        (token,)
    )
    session = cursor.fetchone()
    
    if session:
        return jsonify({
            "authenticated": True,
            "user": {
                "id": session['user_id'],
                "username": session['username'],
                "email": session['email']
            }
        }), 200
    else:
        return jsonify({"authenticated": False, "message": "Invalid or expired token"}), 401

@app.route('/api/instances', methods=['GET'])
def get_instances():
    """ユーザーのインスタンス一覧を取得"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({"success": False, "message": "No token provided"}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # トークンからユーザーIDを取得
    cursor.execute(
        'SELECT user_id FROM sessions WHERE token = ? AND expires_at > CURRENT_TIMESTAMP',
        (token,)
    )
    session = cursor.fetchone()
    
    if not session:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 401
    
    user_id = session['user_id']
    
    # ユーザーのインスタンス一覧を取得
    cursor.execute(
        '''
        SELECT id, subdomain, ip_address, port, status, created_at, last_active
        FROM instances
        WHERE user_id = ?
        ORDER BY created_at DESC
        ''',
        (user_id,)
    )
    instances = cursor.fetchall()
    
    result = []
    for instance in instances:
        result.append({
            "id": instance['id'],
            "subdomain": instance['subdomain'],
            "url": f"https://{instance['subdomain']}.teai.io",
            "status": instance['status'],
            "created_at": instance['created_at'],
            "last_active": instance['last_active']
        })
    
    return jsonify({"success": True, "instances": result}), 200

@app.route('/api/instances', methods=['POST'])
def create_instance():
    """新しいインスタンスを作成"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({"success": False, "message": "No token provided"}), 401
    
    data = request.get_json()
    subdomain = data.get('subdomain')
    
    if not subdomain:
        return jsonify({"success": False, "message": "Subdomain is required"}), 400
    
    # サブドメインのバリデーション
    if not subdomain.isalnum() or len(subdomain) < 3 or len(subdomain) > 20:
        return jsonify({
            "success": False,
            "message": "Subdomain must be alphanumeric and between 3-20 characters"
        }), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # トークンからユーザーIDを取得
    cursor.execute(
        'SELECT user_id FROM sessions WHERE token = ? AND expires_at > CURRENT_TIMESTAMP',
        (token,)
    )
    session = cursor.fetchone()
    
    if not session:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 401
    
    user_id = session['user_id']
    
    # サブドメインの重複チェック
    cursor.execute('SELECT id FROM instances WHERE subdomain = ?', (subdomain,))
    if cursor.fetchone():
        return jsonify({"success": False, "message": "Subdomain already exists"}), 409
    
    # 新しいインスタンスを作成
    instance_id = str(uuid.uuid4())
    ip_address = "127.0.0.1"  # 実際の環境では動的に割り当てる
    port = 3000  # 実際の環境では動的に割り当てる
    
    try:
        cursor.execute(
            '''
            INSERT INTO instances (id, user_id, subdomain, ip_address, port, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (instance_id, user_id, subdomain, ip_address, port, "provisioning")
        )
        db.commit()
        
        # ここで実際のインスタンスをプロビジョニングするコードを追加
        # 例: AWS EC2インスタンスの起動など
        
        # プロビジョニングが完了したら、ステータスを更新
        cursor.execute(
            'UPDATE instances SET status = ? WHERE id = ?',
            ("active", instance_id)
        )
        db.commit()
        
        # Nginx設定を更新
        update_nginx_config()
        
        return jsonify({
            "success": True,
            "message": "Instance created successfully",
            "instance": {
                "id": instance_id,
                "subdomain": subdomain,
                "url": f"https://{subdomain}.teai.io",
                "status": "active"
            }
        }), 201
    except Exception as e:
        logger.error(f"Instance creation error: {e}")
        return jsonify({"success": False, "message": "Failed to create instance"}), 500

@app.route('/api/instances/<instance_id>', methods=['DELETE'])
def delete_instance(instance_id):
    """インスタンスを削除"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({"success": False, "message": "No token provided"}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # トークンからユーザーIDを取得
    cursor.execute(
        'SELECT user_id FROM sessions WHERE token = ? AND expires_at > CURRENT_TIMESTAMP',
        (token,)
    )
    session = cursor.fetchone()
    
    if not session:
        return jsonify({"success": False, "message": "Invalid or expired token"}), 401
    
    user_id = session['user_id']
    
    # インスタンスの所有者確認
    cursor.execute(
        'SELECT id, subdomain FROM instances WHERE id = ? AND user_id = ?',
        (instance_id, user_id)
    )
    instance = cursor.fetchone()
    
    if not instance:
        return jsonify({"success": False, "message": "Instance not found or not owned by user"}), 404
    
    try:
        # ここで実際のインスタンスを削除するコードを追加
        # 例: AWS EC2インスタンスの終了など
        
        # データベースからインスタンスを削除
        cursor.execute('DELETE FROM instances WHERE id = ?', (instance_id,))
        db.commit()
        
        # Nginx設定を更新
        update_nginx_config()
        
        return jsonify({"success": True, "message": "Instance deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Instance deletion error: {e}")
        return jsonify({"success": False, "message": "Failed to delete instance"}), 500

if __name__ == '__main__':
    # データベースの初期化
    with app.app_context():
        init_db()
    
    # アプリケーションの起動
    app.run(host='127.0.0.1', port=5000)