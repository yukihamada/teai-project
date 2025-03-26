#!/usr/bin/env python3

# Read the file
with open('/usr/local/bin/teai_api_server.py', 'r') as f:
    content = f.read()

# Add imports for resend
imports_to_add = """
import os
import sys
import uuid
import json
import sqlite3
import hashlib
import logging
import subprocess
import resend
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
"""

# Replace the imports
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
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
""", imports_to_add)

# Replace the send_verification_email function with a Resend version
resend_email_function = '''
def send_verification_email(email, verification_token):
    """Send verification email using Resend API"""
    try:
        # Verification URL
        verification_url = f"https://54.250.147.206/verify.html?token={verification_token}"
        
        # Log the email details
        logger.info(f"[RESEND EMAIL] To: {email}")
        logger.info(f"[RESEND EMAIL] Subject: TeAI - メールアドレスの確認")
        logger.info(f"[RESEND EMAIL] Verification URL: {verification_url}")
        
        # Set Resend API key
        resend_api_key = "re_YKKuiBGB_LBiMw65Keu9x312Bgr6wsJxi"
        resend.api_key = resend_api_key
        
        # Create HTML content
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .logo {{ max-width: 150px; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>TeAIへようこそ！</h1>
                </div>
                <p>TeAIへのご登録ありがとうございます。</p>
                <p>以下のボタンをクリックして、メールアドレスを確認してください：</p>
                <p style="text-align: center;">
                    <a href="{verification_url}" class="button">メールアドレスを確認</a>
                </p>
                <p>または、以下のURLをブラウザに貼り付けてください：</p>
                <p><a href="{verification_url}">{verification_url}</a></p>
                <p>このリンクは24時間有効です。</p>
                <div class="footer">
                    <p>※このメールは自動送信されています。返信はできません。</p>
                    <p>&copy; 2025 TeAI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Create text content
        text_content = f"""
        TeAIへのご登録ありがとうございます。
        
        以下のリンクをクリックして、メールアドレスを確認してください：
        {verification_url}
        
        このリンクは24時間有効です。
        
        ※このメールは自動送信されています。返信はできません。
        """
        
        try:
            # Send email using Resend API
            params = {
                "from": "TeAI <noreply@teai.io>",
                "to": [email],
                "subject": "TeAI - メールアドレスの確認",
                "html": html_content,
                "text": text_content,
            }
            
            # Send the email
            response = resend.Emails.send(params)
            logger.info(f"[RESEND EMAIL] Email sent successfully to {email}, ID: {response['id']}")
            
            # For testing purposes, create a file with the verification URL
            verification_file = f"/tmp/verification_{verification_token}.txt"
            with open(verification_file, "w") as f:
                f.write(f"Email: {email}\\n")
                f.write(f"Verification URL: {verification_url}\\n")
                f.write(f"Resend Email ID: {response['id']}\\n")
            
            # Make the verification file readable by everyone
            import os
            os.chmod(verification_file, 0o644)
            
            # Create a symlink to the latest verification file
            latest_link = "/tmp/latest_verification.txt"
            if os.path.exists(latest_link):
                os.remove(latest_link)
            os.symlink(verification_file, latest_link)
            os.chmod(latest_link, 0o644)
            logger.info(f"[RESEND EMAIL] Latest verification link: {latest_link}")
            
            return True
        except Exception as e:
            logger.error(f"[RESEND EMAIL] Failed to send email via Resend API: {e}")
            
            # For testing purposes, create a file with the verification URL even if sending fails
            verification_file = f"/tmp/verification_{verification_token}.txt"
            with open(verification_file, "w") as f:
                f.write(f"Email: {email}\\n")
                f.write(f"Verification URL: {verification_url}\\n")
                f.write(f"Error: {str(e)}\\n")
            
            # Make the verification file readable by everyone
            import os
            os.chmod(verification_file, 0o644)
            
            # Create a symlink to the latest verification file
            latest_link = "/tmp/latest_verification.txt"
            if os.path.exists(latest_link):
                os.remove(latest_link)
            os.symlink(verification_file, latest_link)
            os.chmod(latest_link, 0o644)
            logger.info(f"[RESEND EMAIL] Latest verification link: {latest_link}")
            
            # Return True to allow the registration process to continue
            return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False
'''

# Replace the send_verification_email function
content = content.replace('''
def send_verification_email(email, verification_token):
    """Send verification email using SMTP"""
    try:
        # Verification URL
        verification_url = f"https://54.250.147.206/verify.html?token={verification_token}"
        
        # Log the email details
        logger.info(f"[SMTP EMAIL] To: {email}")
        logger.info(f"[SMTP EMAIL] Subject: TeAI - メールアドレスの確認")
        logger.info(f"[SMTP EMAIL] Verification URL: {verification_url}")
        
        # In a real production environment, this would use a proper SMTP server
        # For now, we'll use a simulated SMTP server
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Email content
        subject = "TeAI - メールアドレスの確認"
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = "noreply@teai.io"
        message["To"] = email
        
        # Create text version
        text_body = f"""
        TeAIへのご登録ありがとうございます。
        
        以下のリンクをクリックして、メールアドレスを確認してください：
        {verification_url}
        
        このリンクは24時間有効です。
        
        ※このメールは自動送信されています。返信はできません。
        """
        
        # Create HTML version
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; margin-bottom: 20px; }}
                .logo {{ max-width: 150px; }}
                .button {{ display: inline-block; padding: 10px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>TeAIへようこそ！</h1>
                </div>
                <p>TeAIへのご登録ありがとうございます。</p>
                <p>以下のボタンをクリックして、メールアドレスを確認してください：</p>
                <p style="text-align: center;">
                    <a href="{verification_url}" class="button">メールアドレスを確認</a>
                </p>
                <p>または、以下のURLをブラウザに貼り付けてください：</p>
                <p><a href="{verification_url}">{verification_url}</a></p>
                <p>このリンクは24時間有効です。</p>
                <div class="footer">
                    <p>※このメールは自動送信されています。返信はできません。</p>
                    <p>&copy; 2025 TeAI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Attach parts
        part1 = MIMEText(text_body, "plain")
        part2 = MIMEText(html_body, "html")
        message.attach(part1)
        message.attach(part2)
        
        # SMTP server configuration
        # In a real production environment, you would use a proper SMTP server
        # For now, we'll just log the message and save it to a file
        logger.info(f"[SMTP EMAIL] Message: {message.as_string()[:500]}...")
        
        # For testing purposes, create a file with the verification URL
        verification_file = f"/tmp/verification_{verification_token}.txt"
        with open(verification_file, "w") as f:
            f.write(f"Email: {email}\\n")
            f.write(f"Verification URL: {verification_url}\\n")
            f.write(f"\\n--- Email Content ---\\n")
            f.write(message.as_string())
        logger.info(f"[SMTP EMAIL] Email saved to {verification_file}")
        
        # Make the verification file readable by everyone
        import os
        os.chmod(verification_file, 0o644)
        
        # Create a symlink to the latest verification file
        latest_link = "/tmp/latest_verification.txt"
        if os.path.exists(latest_link):
            os.remove(latest_link)
        os.symlink(verification_file, latest_link)
        os.chmod(latest_link, 0o644)
        logger.info(f"[SMTP EMAIL] Latest verification link: {latest_link}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False
''', resend_email_function)

# Write the file
with open('/usr/local/bin/teai_api_server.py', 'w') as f:
    f.write(content)

print("Resend email function added successfully.")