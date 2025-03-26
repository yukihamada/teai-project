#!/usr/bin/env python3
import json
import logging
import os
import hashlib
import time
import subprocess
import uuid
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, g, render_template_string
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/teai-backend.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("teai-backend")

app = Flask(__name__)
CORS(app)

# 設定
DATABASE_PATH = '/var/lib/teai/teai.db'
NGINX_CONFIG_PATH = '/etc/nginx/conf.d/teai_instances.conf'
VERIFICATION_EXPIRY_HOURS = 24
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USERNAME = 'teai.service@gmail.com'  # 実際のメールアドレスに変更
SMTP_PASSWORD = 'your_app_password'  # Gmailのアプリパスワードに変更
EMAIL_FROM = 'TeAI <teai.service@gmail.com>'
BASE_URL = 'http://54.250.147.206'  # 実際のドメインに変更（後でteai.ioに）

# Nginxマッピング設定テンプレート
NGINX_MAP_TEMPLATE = """
# TeAI インスタンスマッピング - 自動生成されたファイルです
# 最終更新: {timestamp}

map $http_host $backend_server {{
    default "127.0.0.1:3000";  # デフォルトサーバー
{instance_mappings}
}}
"""

# メール認証テンプレート
VERIFICATION_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
        }
        .container {
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        .header {
            background-color: #3498db;
            color: white;
            padding: 10px 20px;
            border-radius: 5px 5px 0 0;
            margin-bottom: 20px;
        }
        .button {
            display: inline-block;
            background-color: #3498db;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            margin-top: 20px;
            font-size: 12px;
            color: #777;
            border-top: 1px solid #ddd;
            padding-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>TeAI メールアドレスの確認</h2>
        </div>
        <p>こんにちは、{{username}}さん</p>
        <p>TeAIへのご登録ありがとうございます。以下のリンクをクリックして、メールアドレスの確認を完了してください。</p>
        <p><a href="{{verification_url}}" class="button">メールアドレスを確認する</a></p>
        <p>または、以下のリンクをブラウザに貼り付けてください：</p>
        <p>{{verification_url}}</p>
        <p>このリンクは{{expiry_hours}}時間後に期限切れとなります。</p>
        <div class="footer">
            <p>このメールは自動送信されています。返信しないでください。</p>
            <p>&copy; 2025 TeAI All rights reserved.</p>
        </div>
    </div>
</body>
</html>
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
            first_name TEXT,
            last_name TEXT,
            is_verified BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        ''')
        
        # 検証トークンテーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        # インスタンステーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS instances (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            subdomain TEXT UNIQUE NOT NULL,
            port INTEGER NOT NULL,
            status TEXT NOT NULL,
            container_id TEXT,
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
        cursor.execute('SELECT subdomain, port FROM instances WHERE status = "active"')
        instances = cursor.fetchall()
        
        mappings = []
        for instance in instances:
            mappings.append(f'    "{instance["subdomain"]}.teai.io" "127.0.0.1:{instance["port"]}";')
        
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

def send_verification_email(user_id, username, email):
    """検証メールを送信"""
    # 検証トークンの生成
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(hours=VERIFICATION_EXPIRY_HOURS)
    
    # トークンをデータベースに保存
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # 既存のトークンを削除
        cursor.execute('DELETE FROM verification_tokens WHERE user_id = ?', (user_id,))
        
        # 新しいトークンを追加
        token_id = str(uuid.uuid4())
        cursor.execute(
            'INSERT INTO verification_tokens (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)',
            (token_id, user_id, token, expires_at)
        )
        db.commit()
    
    # 検証URLの作成
    verification_url = f"{BASE_URL}/verify-email?token={token}"
    
    # メールの作成
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'TeAI メールアドレスの確認'
    msg['From'] = EMAIL_FROM
    msg['To'] = email
    
    # HTMLメールの作成
    html_content = render_template_string(
        VERIFICATION_EMAIL_TEMPLATE,
        username=username,
        verification_url=verification_url,
        expiry_hours=VERIFICATION_EXPIRY_HOURS
    )
    
    msg.attach(MIMEText(html_content, 'html'))
    
    # メールの送信
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"Verification email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False

def create_instance_for_user(user_id, subdomain):
    """ユーザー用のインスタンスを作成"""
    # 利用可能なポートを見つける（3001から開始）
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('SELECT port FROM instances ORDER BY port DESC LIMIT 1')
        result = cursor.fetchone()
        
        if result:
            port = result['port'] + 1
        else:
            port = 3001
        
        # インスタンスの作成
        instance_id = str(uuid.uuid4())
        
        # Dockerコンテナの起動
        try:
            container_name = f"teai-{subdomain}"
            
            # 既存のコンテナを確認
            check_cmd = f"docker ps -a --filter name={container_name} --format '{{{{.ID}}}}'"
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            if result.stdout.strip():
                # 既存のコンテナを削除
                subprocess.run(f"docker rm -f {container_name}", shell=True, check=True)
            
            # 新しいコンテナを起動
            cmd = f"""
            docker run -d --rm \
              -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.30-nikolaik \
              -e LOG_ALL_EVENTS=true \
              -v /var/run/docker.sock:/var/run/docker.sock \
              -v /root/.teai-state/{subdomain}:/.teai-state \
              -p {port}:3000 \
              --add-host host.docker.internal:host-gateway \
              --name {container_name} \
              docker.all-hands.dev/all-hands-ai/openhands:0.30
            """
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            container_id = result.stdout.strip()
            
            # インスタンス情報をデータベースに保存
            cursor.execute(
                '''
                INSERT INTO instances (id, user_id, subdomain, port, status, container_id)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (instance_id, user_id, subdomain, port, "active", container_id)
            )
            db.commit()
            
            # Nginx設定を更新
            update_nginx_config()
            
            logger.info(f"Instance created for user {user_id} with subdomain {subdomain}")
            return {
                "id": instance_id,
                "subdomain": subdomain,
                "port": port,
                "status": "active"
            }
        except Exception as e:
            logger.error(f"Failed to create instance: {e}")
            return None

@app.route('/api/register', methods=['POST'])
def register():
    """新規ユーザー登録"""
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    
    if not all([username, email, password]):
        return jsonify({"success": False, "message": "必須項目が不足しています"}), 400
    
    # パスワードハッシュ化
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # ユーザーIDの生成
        user_id = str(uuid.uuid4())
        
        # ユーザーの作成
        cursor.execute(
            '''
            INSERT INTO users (id, username, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (user_id, username, email, password_hash, first_name, last_name)
        )
        db.commit()
        
        # 検証メールの送信
        send_verification_email(user_id, username, email)
        
        return jsonify({
            "success": True,
            "message": "登録が完了しました。メールアドレスの確認をお願いします。",
            "userId": user_id
        }), 201
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed: users.username" in str(e):
            return jsonify({"success": False, "message": "このユーザー名は既に使用されています"}), 409
        elif "UNIQUE constraint failed: users.email" in str(e):
            return jsonify({"success": False, "message": "このメールアドレスは既に登録されています"}), 409
        else:
            logger.error(f"Registration error: {e}")
            return jsonify({"success": False, "message": "登録に失敗しました"}), 500
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"success": False, "message": "登録に失敗しました"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """ユーザーログイン"""
    data = request.get_json()
    username_or_email = data.get('username')  # ユーザー名またはメールアドレス
    password = data.get('password')
    
    if not all([username_or_email, password]):
        return jsonify({"success": False, "message": "ユーザー名/メールアドレスとパスワードを入力してください"}), 400
    
    # パスワードハッシュ化
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    db = get_db()
    cursor = db.cursor()
    
    # ユーザー名またはメールアドレスでユーザーを検索
    cursor.execute(
        '''
        SELECT id, username, email, is_verified, first_name, last_name
        FROM users
        WHERE (username = ? OR email = ?) AND password_hash = ?
        ''',
        (username_or_email, username_or_email, password_hash)
    )
    user = cursor.fetchone()
    
    if user:
        # メール認証が完了しているか確認
        if not user['is_verified']:
            return jsonify({
                "success": False,
                "message": "メールアドレスの確認が完了していません。メールをご確認ください。",
                "needVerification": True,
                "userId": user['id']
            }), 403
        
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
        
        # ユーザーのインスタンスを確認
        cursor.execute(
            'SELECT id, subdomain, port, status FROM instances WHERE user_id = ? AND status = "active"',
            (user['id'],)
        )
        instance = cursor.fetchone()
        
        # インスタンスがない場合は作成
        if not instance:
            # サブドメインはユーザー名をベースに作成
            subdomain = user['username'].lower()
            # 特殊文字を削除
            subdomain = ''.join(c for c in subdomain if c.isalnum())
            
            # サブドメインが既に使用されているか確認
            cursor.execute('SELECT id FROM instances WHERE subdomain = ?', (subdomain,))
            if cursor.fetchone():
                # ランダムな文字列を追加
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
                subdomain = f"{subdomain}{random_suffix}"
            
            # インスタンスを作成
            instance_info = create_instance_for_user(user['id'], subdomain)
            
            if instance_info:
                instance_url = f"http://{subdomain}.teai.io"
            else:
                instance_url = None
        else:
            instance_url = f"http://{instance['subdomain']}.teai.io"
        
        return jsonify({
            "success": True,
            "message": "ログインに成功しました",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "firstName": user['first_name'],
                "lastName": user['last_name']
            },
            "token": token,
            "expires_at": expires_at.isoformat(),
            "instance_url": instance_url
        }), 200
    else:
        return jsonify({"success": False, "message": "ユーザー名/メールアドレスまたはパスワードが正しくありません"}), 401

@app.route('/api/verify-email', methods=['GET'])
def verify_email():
    """メールアドレスの確認"""
    token = request.args.get('token')
    
    if not token:
        return jsonify({"success": False, "message": "無効なトークンです"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # トークンの検証
    cursor.execute(
        '''
        SELECT vt.user_id, vt.expires_at, u.username
        FROM verification_tokens vt
        JOIN users u ON vt.user_id = u.id
        WHERE vt.token = ?
        ''',
        (token,)
    )
    verification = cursor.fetchone()
    
    if not verification:
        return jsonify({"success": False, "message": "無効なトークンです"}), 400
    
    # トークンの有効期限を確認
    if datetime.fromisoformat(verification['expires_at']) < datetime.now():
        return jsonify({"success": False, "message": "トークンの有効期限が切れています"}), 400
    
    # ユーザーを認証済みに更新
    cursor.execute(
        'UPDATE users SET is_verified = 1 WHERE id = ?',
        (verification['user_id'],)
    )
    
    # 使用済みトークンを削除
    cursor.execute(
        'DELETE FROM verification_tokens WHERE token = ?',
        (token,)
    )
    
    db.commit()
    
    # ユーザーのサブドメインを作成
    subdomain = verification['username'].lower()
    # 特殊文字を削除
    subdomain = ''.join(c for c in subdomain if c.isalnum())
    
    # サブドメインが既に使用されているか確認
    cursor.execute('SELECT id FROM instances WHERE subdomain = ?', (subdomain,))
    if cursor.fetchone():
        # ランダムな文字列を追加
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        subdomain = f"{subdomain}{random_suffix}"
    
    # インスタンスを作成
    instance_info = create_instance_for_user(verification['user_id'], subdomain)
    
    if instance_info:
        instance_url = f"http://{subdomain}.teai.io"
        
        # HTML応答を返す
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>メール確認完了 - TeAI</title>
            <style>
                body {{
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #2c3e50;
                    background-color: #ecf0f1;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }}
                .container {{
                    background-color: white;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
                    padding: 40px;
                    text-align: center;
                    max-width: 500px;
                }}
                h1 {{
                    color: #3498db;
                    margin-bottom: 20px;
                }}
                p {{
                    margin-bottom: 20px;
                    color: #7f8c8d;
                }}
                .btn {{
                    display: inline-block;
                    background-color: #3498db;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 5px;
                    text-decoration: none;
                    font-weight: 500;
                    transition: all 0.3s;
                }}
                .btn:hover {{
                    background-color: #2980b9;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>メール確認完了</h1>
                <p>メールアドレスの確認が完了しました。TeAIをご利用いただけます。</p>
                <p>あなた専用のTeAI環境が準備されました：</p>
                <p><a href="{instance_url}" class="btn">TeAI環境にアクセスする</a></p>
                <p>または、以下のURLをブラウザに貼り付けてください：</p>
                <p>{instance_url}</p>
            </div>
        </body>
        </html>
        """
        
        return html_response, 200, {'Content-Type': 'text/html; charset=utf-8'}
    else:
        return jsonify({
            "success": True,
            "message": "メールアドレスの確認が完了しましたが、インスタンスの作成に失敗しました。"
        }), 200

@app.route('/api/resend-verification', methods=['POST'])
def resend_verification():
    """確認メールの再送信"""
    data = request.get_json()
    user_id = data.get('userId')
    
    if not user_id:
        return jsonify({"success": False, "message": "ユーザーIDが必要です"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # ユーザーの確認
    cursor.execute(
        'SELECT id, username, email, is_verified FROM users WHERE id = ?',
        (user_id,)
    )
    user = cursor.fetchone()
    
    if not user:
        return jsonify({"success": False, "message": "ユーザーが見つかりません"}), 404
    
    if user['is_verified']:
        return jsonify({"success": False, "message": "このアカウントは既に認証されています"}), 400
    
    # 確認メールの送信
    if send_verification_email(user['id'], user['username'], user['email']):
        return jsonify({
            "success": True,
            "message": "確認メールを再送信しました。メールをご確認ください。"
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": "確認メールの送信に失敗しました。しばらくしてからもう一度お試しください。"
        }), 500

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """認証状態の確認"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({"authenticated": False, "message": "認証が必要です"}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # セッションの確認
    cursor.execute(
        '''
        SELECT s.user_id, s.expires_at, u.username, u.email, u.first_name, u.last_name
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
        ''',
        (token,)
    )
    session = cursor.fetchone()
    
    if not session:
        return jsonify({"authenticated": False, "message": "無効なトークンです"}), 401
    
    # トークンの有効期限を確認
    if datetime.fromisoformat(session['expires_at']) < datetime.now():
        return jsonify({"authenticated": False, "message": "セッションの有効期限が切れています"}), 401
    
    # ユーザーのインスタンスを確認
    cursor.execute(
        'SELECT subdomain FROM instances WHERE user_id = ? AND status = "active"',
        (session['user_id'],)
    )
    instance = cursor.fetchone()
    
    if instance:
        instance_url = f"http://{instance['subdomain']}.teai.io"
    else:
        instance_url = None
    
    return jsonify({
        "authenticated": True,
        "user": {
            "id": session['user_id'],
            "username": session['username'],
            "email": session['email'],
            "firstName": session['first_name'],
            "lastName": session['last_name']
        },
        "instance_url": instance_url
    }), 200

@app.route('/api/instances', methods=['GET'])
def get_user_instance():
    """ユーザーのインスタンス情報を取得"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({"success": False, "message": "認証が必要です"}), 401
    
    db = get_db()
    cursor = db.cursor()
    
    # セッションの確認
    cursor.execute(
        'SELECT user_id FROM sessions WHERE token = ? AND expires_at > datetime("now")',
        (token,)
    )
    session = cursor.fetchone()
    
    if not session:
        return jsonify({"success": False, "message": "無効なトークンです"}), 401
    
    # ユーザーのインスタンスを確認
    cursor.execute(
        '''
        SELECT id, subdomain, port, status, created_at, last_active
        FROM instances
        WHERE user_id = ?
        ''',
        (session['user_id'],)
    )
    instances = cursor.fetchall()
    
    result = []
    for instance in instances:
        result.append({
            "id": instance['id'],
            "subdomain": instance['subdomain'],
            "url": f"http://{instance['subdomain']}.teai.io",
            "status": instance['status'],
            "created_at": instance['created_at'],
            "last_active": instance['last_active']
        })
    
    return jsonify({
        "success": True,
        "instances": result
    }), 200

@app.route('/api/instances/restart', methods=['POST'])
def restart_instance():
    """インスタンスを再起動"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    data = request.get_json()
    instance_id = data.get('instanceId')
    
    if not token:
        return jsonify({"success": False, "message": "認証が必要です"}), 401
    
    if not instance_id:
        return jsonify({"success": False, "message": "インスタンスIDが必要です"}), 400
    
    db = get_db()
    cursor = db.cursor()
    
    # セッションの確認
    cursor.execute(
        'SELECT user_id FROM sessions WHERE token = ? AND expires_at > datetime("now")',
        (token,)
    )
    session = cursor.fetchone()
    
    if not session:
        return jsonify({"success": False, "message": "無効なトークンです"}), 401
    
    # インスタンスの確認
    cursor.execute(
        '''
        SELECT id, subdomain, container_id
        FROM instances
        WHERE id = ? AND user_id = ?
        ''',
        (instance_id, session['user_id'])
    )
    instance = cursor.fetchone()
    
    if not instance:
        return jsonify({"success": False, "message": "インスタンスが見つかりません"}), 404
    
    try:
        # コンテナの再起動
        container_name = f"teai-{instance['subdomain']}"
        
        # コンテナの停止
        subprocess.run(f"docker stop {container_name}", shell=True, check=True)
        
        # コンテナの起動
        subprocess.run(f"docker start {container_name}", shell=True, check=True)
        
        return jsonify({
            "success": True,
            "message": "インスタンスを再起動しました"
        }), 200
    except Exception as e:
        logger.error(f"Failed to restart instance: {e}")
        return jsonify({
            "success": False,
            "message": "インスタンスの再起動に失敗しました"
        }), 500

@app.route('/verify-email', methods=['GET'])
def verify_email_page():
    """メール確認ページ"""
    token = request.args.get('token')
    
    if not token:
        return "無効なトークンです", 400
    
    # APIエンドポイントにリダイレクト
    return redirect(f"/api/verify-email?token={token}")

# メインページ
@app.route('/')
def index():
    return redirect('/index.html')

if __name__ == '__main__':
    # データベースの初期化
    with app.app_context():
        init_db()
    
    # アプリケーションの起動
    app.run(host='0.0.0.0', port=5000)