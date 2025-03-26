#!/usr/bin/env python3

import sys

# GitHub OAuth設定を取得
github_client_id = input("GitHub Client ID: ")
github_client_secret = input("GitHub Client Secret: ")

# 設定を検証
if not github_client_id or not github_client_secret:
    print("エラー: GitHub OAuth設定が入力されていません。")
    sys.exit(1)

# teai_api_server.pyファイルを読み込む
with open('/usr/local/bin/teai_api_server.py', 'r') as f:
    content = f.read()

# GitHub OAuth設定を置き換え
content = content.replace("GITHUB_CLIENT_ID = \"YOUR_GITHUB_CLIENT_ID\"", f"GITHUB_CLIENT_ID = \"{github_client_id}\"")
content = content.replace("GITHUB_CLIENT_SECRET = \"YOUR_GITHUB_CLIENT_SECRET\"", f"GITHUB_CLIENT_SECRET = \"{github_client_secret}\"")

# 更新したファイルを書き込む
with open('/usr/local/bin/teai_api_server.py', 'w') as f:
    f.write(content)

print("GitHub OAuth設定が正常に設定されました。")