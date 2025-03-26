#!/bin/bash

# === CONFIG ==============================
DOMAIN="teai.io"
EMAIL="admin@teai.io"
# =========================================

# Certbotがインストールされているか確認
if ! command -v certbot &> /dev/null; then
    echo "Certbotがインストールされていません。インストールを開始します..."
    amazon-linux-extras install epel -y
    yum install certbot python3-certbot-nginx -y
fi

# Nginxの設定ファイルを作成
cat > /etc/nginx/conf.d/teai.conf << EOF
server {
    listen 80;
    server_name $DOMAIN *.$DOMAIN;
    
    root /var/www/teai.io;
    index index.html;
    
    location /api/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF

# Nginxの設定をリロード
nginx -t && systemctl reload nginx

# Let's Encryptで証明書を取得
echo "Let's Encryptで証明書を取得します..."
certbot --nginx -d $DOMAIN -d *.$DOMAIN --agree-tos --email $EMAIL --non-interactive

# 証明書の自動更新を確認
echo "証明書の自動更新をテストします..."
certbot renew --dry-run

echo "SSL証明書の設定が完了しました。"
echo "https://$DOMAIN でアクセスできます。"