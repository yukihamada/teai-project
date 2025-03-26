# Route 53でのDNS設定手順

TeAIのドメイン（teai.io）をEC2インスタンスに向けるためのRoute 53設定手順です。

## 1. Route 53ホストゾーンの作成

1. AWSマネジメントコンソールにログインします。
2. Route 53サービスに移動します。
3. 「ホストゾーン」→「ホストゾーンの作成」をクリックします。
4. 以下の情報を入力します：
   - ドメイン名: teai.io
   - タイプ: パブリックホストゾーン
5. 「ホストゾーンの作成」をクリックします。

## 2. DNSレコードの設定

1. 作成したホストゾーンを選択します。
2. 「レコードの作成」をクリックします。
3. 以下の情報を入力して、ルートドメインのAレコードを作成します：
   - レコード名: （空白のまま）
   - レコードタイプ: A
   - 値: 54.250.147.206（EC2インスタンスのIPアドレス）
   - TTL: 300
4. 「レコードの作成」をクリックします。
5. 再度「レコードの作成」をクリックし、ワイルドカードサブドメインのAレコードを作成します：
   - レコード名: *
   - レコードタイプ: A
   - 値: 54.250.147.206（EC2インスタンスのIPアドレス）
   - TTL: 300
6. 「レコードの作成」をクリックします。

## 3. ネームサーバーの設定

1. Route 53ホストゾーンに表示されているネームサーバー（NS）レコードをメモします。
2. ドメインレジストラ（ドメインを購入した会社）の管理画面にログインします。
3. ドメインのネームサーバー設定を変更し、Route 53のネームサーバーを設定します。
4. 変更が反映されるまで最大48時間かかる場合があります。

## 4. DNSの伝播確認

1. 以下のコマンドを使用して、DNSの伝播を確認します：
   ```bash
   dig teai.io
   ```
2. 応答のセクションに、EC2インスタンスのIPアドレス（54.250.147.206）が表示されることを確認します。

## 5. Let's Encryptでの証明書取得

DNSの伝播が完了したら、Let's Encryptを使用して正式なSSL証明書を取得できます：

```bash
sudo certbot certonly --webroot -w /var/www/letsencrypt -d teai.io -d "*.teai.io" --agree-tos --email admin@teai.io --non-interactive
```

ワイルドカード証明書（*.teai.io）を取得するには、DNS-01チャレンジが必要です：

```bash
sudo certbot certonly --manual --preferred-challenges dns -d teai.io -d "*.teai.io" --agree-tos --email admin@teai.io
```

証明書が取得できたら、Nginx設定を更新します：

```bash
sudo bash -c 'cat > /etc/nginx/conf.d/teai_ssl.conf << EOF
# SSL設定
server {
    listen 443 ssl;
    server_name teai.io *.teai.io;

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
    server_name teai.io *.teai.io;
    
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

sudo nginx -t && sudo systemctl reload nginx
```

## 6. 証明書の自動更新

Let's Encryptの証明書は90日ごとに更新が必要です。自動更新を設定します：

```bash
sudo bash -c 'echo "0 0,12 * * * root python -c \"import random; import time; time.sleep(random.random() * 3600)\" && certbot renew -q" | sudo tee -a /etc/crontab > /dev/null'
```