#!/usr/bin/env python3
import os

# バックエンドファイルのパス
backend_file = '/usr/local/bin/teai_backend.py'

# ファイルを読み込む
with open(backend_file, 'r') as f:
    content = f.read()

# メール送信関数を修正
old_function = """def send_verification_email(user_id, username, email):
    """
new_function = """def send_verification_email(user_id, username, email):
    # 実際のメール送信の代わりにファイルに保存
    verification_dir = "/var/www/teai.io/verification"
    os.makedirs(verification_dir, exist_ok=True)
    """

content = content.replace(old_function, new_function)

# SMTP部分を修正
old_smtp = """    # メールの送信
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
        return False"""

new_smtp = """    # メールの送信（ファイルに保存）
    try:
        # メール内容をファイルに保存
        verification_file = os.path.join(verification_dir, f"{user_id}.html")
        with open(verification_file, "w") as f:
            f.write(html_content)
        
        # 検証URLをログに出力
        logger.info(f"Verification URL for {username}: {verification_url}")
        return True
    except Exception as e:
        logger.error(f"Failed to save verification email: {e}")
        return False"""

content = content.replace(old_smtp, new_smtp)

# 修正したファイルを保存
with open(backend_file, 'w') as f:
    f.write(content)

print("メール送信機能の修正が完了しました。")