#!/usr/bin/env python3

# GitHub OAuth認証を実装するスクリプト
# APIサーバーのコードを修正して、GitHub認証を追加します

# GitHub OAuth設定
GITHUB_CLIENT_ID = "YOUR_GITHUB_CLIENT_ID"
GITHUB_CLIENT_SECRET = "YOUR_GITHUB_CLIENT_SECRET"
GITHUB_CALLBACK_URL = "https://teai.io/api/auth/github/callback"

# APIサーバーのコードを読み込む
with open('/usr/local/bin/teai_api_server.py', 'r') as f:
    content = f.read()

# 必要なインポートを追加
imports_to_add = """
import os
import sys
import uuid
import json
import sqlite3
import hashlib
import logging
import subprocess
import boto3
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
"""

# 既存のインポートを置き換え
content = content.replace("""
import os
import sys
import uuid
import json
import sqlite3
import hashlib
import logging
import subprocess
import boto3
import time
import random
import string
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
""", imports_to_add)

# GitHub OAuth設定を追加
github_config = f"""
# GitHub OAuth設定
GITHUB_CLIENT_ID = "{GITHUB_CLIENT_ID}"
GITHUB_CLIENT_SECRET = "{GITHUB_CLIENT_SECRET}"
GITHUB_CALLBACK_URL = "{GITHUB_CALLBACK_URL}"
"""

# AWS設定の後にGitHub設定を追加
content = content.replace("""
# 送信元メールアドレス（SESで検証済みのアドレス）
SENDER_EMAIL = 'noreply@teai.io'
""", """
# 送信元メールアドレス（SESで検証済みのアドレス）
SENDER_EMAIL = 'noreply@teai.io'

""" + github_config)

# アプリケーション設定にセッションキーを追加
content = content.replace("""
# アプリケーション設定
app = Flask(__name__)
CORS(app)
""", """
# アプリケーション設定
app = Flask(__name__)
app.secret_key = os.urandom(24)  # セッション用のシークレットキー
CORS(app)
""")

# GitHub認証エンドポイントを追加
github_auth_endpoints = """
@app.route('/api/auth/github', methods=['GET'])
def github_auth():
    \"\"\"GitHub認証を開始\"\"\"
    # GitHubの認証URLにリダイレクト
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&redirect_uri={GITHUB_CALLBACK_URL}&scope=user:email"
    return redirect(github_auth_url)

@app.route('/api/auth/github/callback', methods=['GET'])
def github_callback():
    \"\"\"GitHub認証のコールバック\"\"\"
    # 認証コードを取得
    code = request.args.get('code')
    if not code:
        return jsonify({"success": False, "message": "Authorization code required"}), 400
    
    # アクセストークンを取得
    response = requests.post(
        'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        data={
            'client_id': GITHUB_CLIENT_ID,
            'client_secret': GITHUB_CLIENT_SECRET,
            'code': code,
            'redirect_uri': GITHUB_CALLBACK_URL
        }
    )
    
    if response.status_code != 200:
        return jsonify({"success": False, "message": "Failed to get access token"}), 400
    
    access_token = response.json().get('access_token')
    if not access_token:
        return jsonify({"success": False, "message": "Access token not found"}), 400
    
    # ユーザー情報を取得
    user_response = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'token {access_token}'}
    )
    
    if user_response.status_code != 200:
        return jsonify({"success": False, "message": "Failed to get user info"}), 400
    
    user_data = user_response.json()
    github_id = str(user_data.get('id'))
    username = user_data.get('login')
    
    # メールアドレスを取得
    email_response = requests.get(
        'https://api.github.com/user/emails',
        headers={'Authorization': f'token {access_token}'}
    )
    
    if email_response.status_code != 200:
        return jsonify({"success": False, "message": "Failed to get user emails"}), 400
    
    emails = email_response.json()
    primary_email = next((email['email'] for email in emails if email['primary']), None)
    
    if not primary_email:
        return jsonify({"success": False, "message": "Primary email not found"}), 400
    
    # データベースに接続
    db = get_db()
    cursor = db.cursor()
    
    # GitHubアカウントが既に登録されているか確認
    cursor.execute('SELECT * FROM users WHERE github_id = ?', (github_id,))
    user = cursor.fetchone()
    
    if not user:
        # 新規ユーザー登録
        # まず、同じメールアドレスのユーザーがいないか確認
        cursor.execute('SELECT * FROM users WHERE email = ?', (primary_email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            # 既存ユーザーにGitHub IDを紐付け
            cursor.execute('UPDATE users SET github_id = ? WHERE id = ?', (github_id, existing_user['id']))
            user_id = existing_user['id']
        else:
            # 新規ユーザーを作成
            cursor.execute(
                'INSERT INTO users (username, email, password, created_at, is_verified, github_id) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?, ?)',
                (username, primary_email, hashlib.sha256(os.urandom(24)).hexdigest(), True, github_id)
            )
            user_id = cursor.lastrowid
    else:
        user_id = user['id']
    
    # セッショントークンを生成
    session_token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    
    # セッションを保存
    cursor.execute(
        'INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)',
        (session_token, user_id, expires_at)
    )
    
    db.commit()
    db.close()
    
    # フロントエンドにリダイレクト（トークンを含む）
    return redirect(f"/auth-callback?token={session_token}")
"""

# GitHub認証エンドポイントを追加（OpenHandsリダイレクトの前に）
content = content.replace("""
@app.route('/openhands', methods=['GET'])
def redirect_to_openhands():""", github_auth_endpoints + """

@app.route('/openhands', methods=['GET'])
def redirect_to_openhands():""")

# データベース初期化にgithub_idカラムを追加
content = content.replace("""
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        is_verified BOOLEAN NOT NULL DEFAULT 0,
        is_admin BOOLEAN NOT NULL DEFAULT 0
    )
    ''')""", """
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL,
        is_verified BOOLEAN NOT NULL DEFAULT 0,
        is_admin BOOLEAN NOT NULL DEFAULT 0,
        github_id TEXT
    )
    ''')""")

# 更新したコードを書き込む
with open('/usr/local/bin/teai_api_server.py', 'w') as f:
    f.write(content)

print("GitHub認証機能を実装しました。")