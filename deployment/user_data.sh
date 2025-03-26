#!/bin/bash -xe
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

# システムの更新
yum update -y
amazon-linux-extras install docker nginx python3 -y
yum install -y jq sqlite

# 必要なディレクトリの作成
mkdir -p /var/www/teai.io/static/images
mkdir -p /var/lib/teai
mkdir -p /etc/nginx/conf.d

# Nginxの設定
systemctl enable nginx
systemctl start nginx

# Dockerの設定
systemctl enable docker
systemctl start docker

# TeAIイメージのプル（一時的にOpenHandsのイメージを使用）
docker pull docker.all-hands.dev/all-hands-ai/runtime:0.30-nikolaik
docker pull docker.all-hands.dev/all-hands-ai/openhands:0.30

# TeAIコンテナの起動
docker run -d --rm \
  -e SANDBOX_RUNTIME_CONTAINER_IMAGE=docker.all-hands.dev/all-hands-ai/runtime:0.30-nikolaik \
  -e LOG_ALL_EVENTS=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /root/.teai-state:/.teai-state \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  --name teai-app \
  docker.all-hands.dev/all-hands-ai/openhands:0.30

# 起動完了のマーク
touch /tmp/teai_setup_complete