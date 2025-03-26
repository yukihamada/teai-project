#!/bin/bash

# Let's Encryptで証明書を取得
sudo certbot certonly --webroot -w /var/www/letsencrypt -d teai.io --agree-tos --email admin@teai.io --non-interactive

# 証明書が取得できたか確認
if [ -d "/etc/letsencrypt/live/teai.io" ]; then
    echo "証明書の取得に成功しました。"
    
    # SSL設定を作成
    sudo bash -c 'cat > /etc/nginx/conf.d/teai_ssl.conf << EOF
# SSL設定
server {
    listen 443 ssl;
    server_name teai.io;

    # Let\'s Encrypt証明書
    ssl_certificate /etc/letsencrypt/live/teai.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/teai.io/privkey.pem;

    # SSL設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # ルートディレクトリ
    root /var/www/teai.io;
    index index.html;

    # Let\'s Encrypt認証用
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }

    # APIリクエストのプロキシ
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 静的ファイル
    location /static/ {
        alias /var/www/teai.io/static/;
        expires 30d;
    }

    # その他のリクエスト
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}

# HTTPからHTTPSへのリダイレクト
server {
    listen 80;
    server_name teai.io;
    
    # Let\'s Encrypt認証用
    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }
    
    # その他のリクエストはHTTPSにリダイレクト
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF'

    # Nginxの設定をリロード
    sudo nginx -t && sudo systemctl reload nginx
    
    echo "SSL設定が完了しました。"
    echo "https://teai.io でアクセスできます。"
    
    # 証明書の自動更新を設定
    echo "証明書の自動更新を設定します..."
    sudo bash -c 'echo "0 0,12 * * * root python -c \"import random; import time; time.sleep(random.random() * 3600)\" && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null'
    
    echo "セットアップが完了しました。"
else
    echo "証明書の取得に失敗しました。"
    echo "DNSの伝播が完了していない可能性があります。"
    echo "しばらく待ってから再試行してください。"
fi