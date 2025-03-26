# Cloudflareを使用したSSL証明書の設定手順

Cloudflareは無料のSSL証明書とDNSサービスを提供しています。以下の手順でCloudflareを設定し、teai.ioドメインにSSL証明書を適用します。

## 1. Cloudflareアカウントの作成

1. [Cloudflare](https://www.cloudflare.com/)にアクセスし、アカウントを作成またはログインします。
2. ダッシュボードから「サイトを追加」をクリックします。
3. ドメイン名（teai.io）を入力し、「サイトを追加」をクリックします。
4. 無料プランを選択します。

## 2. DNSレコードの設定

1. Cloudflareが現在のDNSレコードをスキャンします。
2. 以下のDNSレコードを追加または確認します：
   - タイプ: A
   - 名前: @（ルートドメイン）
   - コンテンツ: 54.250.147.206（EC2インスタンスのIPアドレス）
   - TTL: 自動
   - プロキシステータス: プロキシ済み（オレンジの雲アイコン）

3. ワイルドカードサブドメインのレコードを追加：
   - タイプ: A
   - 名前: *（ワイルドカード）
   - コンテンツ: 54.250.147.206（EC2インスタンスのIPアドレス）
   - TTL: 自動
   - プロキシステータス: プロキシ済み（オレンジの雲アイコン）

## 3. ネームサーバーの変更

1. Cloudflareが提供するネームサーバーをメモします。
2. ドメインレジストラ（ドメインを購入した会社）の管理画面にログインします。
3. ドメインのネームサーバー設定を変更し、Cloudflareのネームサーバーを設定します。
4. 変更が反映されるまで最大48時間かかる場合があります。

## 4. SSL設定

1. Cloudflareダッシュボードの「SSL/TLS」セクションに移動します。
2. 「概要」タブで、暗号化モードを「フル」または「フル（厳格）」に設定します。
3. 「エッジ証明書」タブで、常時HTTPS（Always Use HTTPS）を有効にします。
4. 「オリジンサーバー」タブで、オリジンサーバー証明書を作成することもできます。

## 5. ページルールの設定（オプション）

1. 「ページルール」セクションに移動します。
2. 「ページルールを作成」をクリックします。
3. 以下のルールを追加して、HTTPSへのリダイレクトを強制します：
   - URL一致: http://*teai.io/*
   - 設定: 常時HTTPS

## 6. EC2インスタンスのNginx設定

EC2インスタンスのNginx設定を更新して、Cloudflareからのリクエストを受け入れるようにします：

```bash
sudo bash -c 'cat > /etc/nginx/conf.d/teai_cloudflare.conf << EOF
# Cloudflare設定
server {
    listen 80;
    server_name teai.io *.teai.io;
    
    # ルートディレクトリ
    root /var/www/teai.io;
    index index.html;
    
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
EOF'

# 既存のSSL設定を削除
sudo rm /etc/nginx/conf.d/teai_ssl.conf

# Nginxの設定をリロード
sudo nginx -t && sudo systemctl reload nginx
```

## 7. 確認

1. Cloudflareダッシュボードの「概要」タブで、ステータスが「アクティブ」になっていることを確認します。
2. ブラウザで `https://teai.io` にアクセスし、サイトが正常に表示されることを確認します。
3. ブラウザのアドレスバーに鍵アイコンが表示され、SSL証明書が有効であることを確認します。

## 注意事項

- Cloudflareのネームサーバーへの変更が反映されるまで、最大48時間かかる場合があります。
- Cloudflareを使用すると、トラフィックはCloudflareのサーバーを経由してEC2インスタンスに転送されます。
- Cloudflareの無料プランには、DDoS保護、CDN、基本的なファイアウォールなどの機能が含まれています。