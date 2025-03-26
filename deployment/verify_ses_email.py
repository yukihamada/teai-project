#!/usr/bin/env python3

import boto3
import sys

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

def verify_email_identity(email):
    """SESでメールアドレスを検証する"""
    try:
        # 検証リクエストを送信
        response = ses_client.verify_email_identity(
            EmailAddress=email
        )
        print(f"検証メールが {email} に送信されました。メールを確認して検証を完了してください。")
        return True
    except Exception as e:
        print(f"メールアドレスの検証に失敗しました: {e}")
        return False

def list_identities():
    """検証済みのメールアドレス一覧を表示"""
    try:
        response = ses_client.list_identities(
            IdentityType='EmailAddress',
            MaxItems=100
        )
        
        print("検証済みのメールアドレス:")
        for identity in response['Identities']:
            status = ses_client.get_identity_verification_attributes(
                Identities=[identity]
            )
            verification_status = status['VerificationAttributes'].get(identity, {}).get('VerificationStatus', 'Unknown')
            print(f"- {identity}: {verification_status}")
        
        return response['Identities']
    except Exception as e:
        print(f"検証済みメールアドレスの取得に失敗しました: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  検証済みメールアドレス一覧を表示: python3 verify_ses_email.py list")
        print("  メールアドレスを検証: python3 verify_ses_email.py verify email@example.com")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_identities()
    elif command == "verify" and len(sys.argv) >= 3:
        email = sys.argv[2]
        verify_email_identity(email)
    else:
        print("無効なコマンドです。")
        print("使用方法:")
        print("  検証済みメールアドレス一覧を表示: python3 verify_ses_email.py list")
        print("  メールアドレスを検証: python3 verify_ses_email.py verify email@example.com")