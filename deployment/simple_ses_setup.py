#!/usr/bin/env python3

import boto3
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# AWS認証情報
AWS_ACCESS_KEY = "YOUR_AWS_ACCESS_KEY"
AWS_SECRET_KEY = "YOUR_AWS_SECRET_KEY"
AWS_REGION = "ap-northeast-1"

# SESクライアントを初期化
ses_client = boto3.client(
    'ses',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# 送信元メールアドレス（SESで検証済みのアドレス）
SENDER_EMAIL = "noreply@teai.io"

def send_verification_email(email, username, verification_token):
    """Send verification email using Amazon SES"""
    try:
        # メールの件名と本文
        subject = "Te🖐️AI - メールアドレスの確認"
        
        # HTML形式のメール本文
        html_body = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>メールアドレスの確認</title>
            <style>
                body {{
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .logo {{
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .logo img {{
                    max-width: 150px;
                }}
                .container {{
                    background-color: #f9f9f9;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #3b82f6;
                    margin-top: 0;
                    font-size: 24px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #3b82f6;
                    color: white;
                    text-decoration: none;
                    padding: 12px 25px;
                    border-radius: 5px;
                    font-weight: bold;
                    margin: 20px 0;
                }}
                .button:hover {{
                    background-color: #2563eb;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="logo">
                <img src="https://teai.io/static/images/teai-logo.png" alt="Te🖐️AI Logo">
            </div>
            <div class="container">
                <h1>こんにちは、{username}さん</h1>
                <p>Te🖐️AIへのご登録ありがとうございます。以下のボタンをクリックして、メールアドレスを確認してください。</p>
                <div style="text-align: center;">
                    <a href="https://teai.io/verify?token={verification_token}" class="button">メールアドレスを確認する</a>
                </div>
                <p>もしボタンが機能しない場合は、以下のURLをブラウザに貼り付けてください：</p>
                <p><a href="https://teai.io/verify?token={verification_token}">https://teai.io/verify?token={verification_token}</a></p>
                <p>このリンクは24時間有効です。</p>
            </div>
            <div class="footer">
                <p>このメールは自動送信されています。返信はできませんのでご了承ください。</p>
                <p>&copy; 2025 Te🖐️AI. All rights reserved.</p>
            </div>
        </body>
        </html>
        '''
        
        # テキスト形式のメール本文（HTMLメールを表示できないメールクライアント用）
        text_body = f'''
        こんにちは、{username}さん

        Te🖐️AIへのご登録ありがとうございます。以下のリンクをクリックして、メールアドレスを確認してください：
        
        https://teai.io/verify?token={verification_token}
        
        このリンクは24時間有効です。
        
        ※このメールは自動送信されています。返信はできませんのでご了承ください。
        
        © 2025 Te🖐️AI. All rights reserved.
        '''
        
        # MIMEマルチパートメッセージを作成
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = SENDER_EMAIL
        message['To'] = email
        
        # テキストとHTML部分を追加
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        message.attach(part1)
        message.attach(part2)
        
        # SESを使用してメールを送信
        response = ses_client.send_raw_email(
            Source=SENDER_EMAIL,
            Destinations=[email],
            RawMessage={'Data': message.as_string()}
        )
        
        print(f"Verification email sent to {email}, MessageId: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False

# テスト送信
if __name__ == "__main__":
    test_email = input("テスト送信先のメールアドレスを入力してください: ")
    if test_email:
        print(f"{test_email} に確認メールを送信しています...")
        result = send_verification_email(test_email, "テストユーザー", "test-verification-token-123456")
        if result:
            print("メール送信に成功しました！")
        else:
            print("メール送信に失敗しました。")
    else:
        print("メールアドレスが入力されていません。")