#!/usr/bin/env python3
import json
import logging
import os
import hashlib
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    handlers=[
        logging.FileHandler("/var/log/auth-server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("auth-server")

app = Flask(__name__)
CORS(app)

# 簡易的なユーザーデータベース
USERS = {
    "user1": {"password": "password1", "name": "User 1"},
    "user2": {"password": "password2", "name": "User 2"}
}

# セッション管理（本番環境では永続化が必要）
SESSIONS = {}

@app.route('/login', methods=['POST'])
def login():
    logger.info(f"POST request: {request.path}")
    
    # リクエストデータの取得
    data = request.get_json()
    logger.info(f"POST data: {json.dumps(data)}")
    
    username = data.get('username')
    password = data.get('password')
    
    logger.info(f"Login attempt for user: {username}")
    
    # 認証チェック
    if username in USERS and USERS[username]["password"] == password:
        # セッションIDの生成
        session_id = hashlib.md5(f"{username}:{time.time()}".encode()).hexdigest()
        SESSIONS[session_id] = {"username": username, "timestamp": time.time()}
        
        logger.info(f"Login successful for user: {username}, session: {session_id}")
        
        # クッキーとJSONレスポンスを返す
        response = jsonify({"success": True, "message": "Login successful"})
        response.set_cookie('session_id', session_id, httponly=True, secure=True)
        return response
    else:
        logger.info(f"Login failed for user: {username}")
        return jsonify({"success": False, "message": "Invalid username or password"}), 401

@app.route('/auth', methods=['GET'])
def auth():
    logger.info(f"GET request: {request.path}")
    
    # セッションIDの取得
    session_id = request.cookies.get('session_id')
    logger.info(f"Auth request with session_id: {session_id}")
    
    # セッションの検証
    if session_id and session_id in SESSIONS:
        username = SESSIONS[session_id]["username"]
        logger.info(f"Auth successful for user: {username}")
        
        # 認証成功
        response = jsonify({"authenticated": True, "username": username})
        response.headers['X-User-ID'] = username
        return response
    else:
        logger.info("Auth failed: No valid session")
        # 認証失敗
        return jsonify({"authenticated": False, "message": "Not authenticated"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    logger.info(f"POST request: {request.path}")
    
    # セッションIDの取得
    session_id = request.cookies.get('session_id')
    
    # セッションの削除
    if session_id and session_id in SESSIONS:
        username = SESSIONS[session_id]["username"]
        del SESSIONS[session_id]
        logger.info(f"Logout successful for user: {username}")
        
        # クッキーを削除してレスポンスを返す
        response = jsonify({"success": True, "message": "Logout successful"})
        response.set_cookie('session_id', '', expires=0)
        return response
    else:
        logger.info("Logout failed: No valid session")
        return jsonify({"success": False, "message": "Not authenticated"}), 401

if __name__ == '__main__':
    logger.info(f"Starting auth server on port 8080...")
    app.run(host='127.0.0.1', port=8080)