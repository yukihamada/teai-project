# TeAI デプロイガイド

このガイドでは、TeAIをさまざまな環境にデプロイする方法について説明します。

## 目次

1. [ローカル環境へのデプロイ](#ローカル環境へのデプロイ)
2. [AWS へのデプロイ](#aws-へのデプロイ)
3. [マルチテナント環境のセットアップ](#マルチテナント環境のセットアップ)

## ローカル環境へのデプロイ

### 前提条件

- Docker がインストールされていること
- 8GB 以上のメモリ
- 50GB 以上の空きディスク容量

### 手順

1. Docker イメージをプル

```bash
docker pull teai/app:latest
docker pull teai/runtime:latest
```

2. Docker コンテナを起動

```bash
docker run -it --rm \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=teai/runtime:latest \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.teai-state:/.teai-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name teai-app \
    teai/app:latest
```

3. ブラウザで http://localhost:3000 にアクセス

## AWS へのデプロイ

### 前提条件

- AWS アカウント
- AWS CLI がインストールされ、設定済みであること
- jq がインストールされていること

### 手順

1. デプロイスクリプトを実行

```bash
cd deployment
chmod +x aws_setup.sh
./aws_setup.sh
```

2. メニューから「新しいインスタンスを起動」を選択

3. 起動する台数を入力（例: 1）

4. デプロイが完了すると、アクセスURLが表示されます

## マルチテナント環境のセットアップ

### 前提条件

- 複数の TeAI インスタンス
- Nginx がインストールされたリバースプロキシサーバー
- SSL 証明書（Let's Encrypt など）

### 手順

1. リバースプロキシサーバーをセットアップ

```bash
# Nginx のインストール
sudo apt update
sudo apt install -y nginx

# SSL 証明書の取得（Let's Encrypt を使用）
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d teai.io -d www.teai.io
```

2. Nginx の設定ファイルを配置

```bash
# 設定ファイルをコピー
sudo cp nginx_proxy.conf /etc/nginx/conf.d/teai-proxy.conf

# インスタンスの IP アドレスを設定
sudo sed -i 's/INSTANCE_1_IP/実際のIPアドレス/' /etc/nginx/conf.d/teai-proxy.conf
sudo sed -i 's/INSTANCE_2_IP/実際のIPアドレス/' /etc/nginx/conf.d/teai-proxy.conf

# 設定をテスト
sudo nginx -t

# Nginx を再起動
sudo systemctl restart nginx
```

3. 認証サーバーをセットアップ

```bash
# 必要なパッケージをインストール
sudo apt install -y python3-pip
sudo pip3 install flask flask-cors

# 認証サーバーのスクリプトをコピー
sudo cp auth_server.py /usr/local/bin/
sudo chmod +x /usr/local/bin/auth_server.py

# サービスとして登録
sudo tee /etc/systemd/system/auth-server.service > /dev/null << 'EOF'
[Unit]
Description=TeAI Authentication Server
After=network.target

[Service]
ExecStart=/usr/local/bin/auth_server.py
Restart=always
User=www-data
Group=www-data
Environment=PATH=/usr/bin:/usr/local/bin
WorkingDirectory=/tmp

[Install]
WantedBy=multi-user.target
EOF

# サービスを有効化して起動
sudo systemctl daemon-reload
sudo systemctl enable auth-server
sudo systemctl start auth-server
```

4. ログインページを設定

```bash
# ディレクトリを作成
sudo mkdir -p /var/www/html/login
sudo mkdir -p /var/www/html/static/images

# ログインページをコピー
sudo cp login.html /var/www/html/login/index.html

# ロゴをコピー
sudo cp ../docs/images/teai-logo.png /var/www/html/static/images/

# 所有者を設定
sudo chown -R www-data:www-data /var/www/html
```

これで、マルチテナント環境のセットアップが完了しました。https://teai.io にアクセスして、TeAI を利用できます。