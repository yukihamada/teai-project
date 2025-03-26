#!/bin/bash
# TeAIのDockerイメージをビルドするスクリプト

# 設定
TEAI_SRC_DIR="$(pwd)/src"
DOCKER_REPO="teai"
VERSION="latest"

# ソースディレクトリの確認
if [ ! -d "$TEAI_SRC_DIR" ]; then
    echo "エラー: ソースディレクトリが見つかりません。"
    echo "先に customize_openhands.sh を実行してください。"
    exit 1
fi

# Dockerfileの確認
if [ ! -f "$TEAI_SRC_DIR/Dockerfile" ]; then
    echo "エラー: Dockerfileが見つかりません。"
    exit 1
fi

# Dockerイメージのビルド
echo "TeAIのDockerイメージをビルドしています..."
cd $TEAI_SRC_DIR

# アプリケーションイメージのビルド
echo "アプリケーションイメージをビルドしています..."
docker build -t $DOCKER_REPO/app:$VERSION .

# ランタイムイメージのビルド
if [ -d "$TEAI_SRC_DIR/runtime" ]; then
    echo "ランタイムイメージをビルドしています..."
    cd $TEAI_SRC_DIR/runtime
    docker build -t $DOCKER_REPO/runtime:$VERSION .
else
    echo "警告: ランタイムディレクトリが見つかりません。ランタイムイメージはビルドされません。"
fi

echo "Dockerイメージのビルドが完了しました！"
echo "イメージ:"
echo "- $DOCKER_REPO/app:$VERSION"
echo "- $DOCKER_REPO/runtime:$VERSION"

# イメージの確認
echo "ビルドされたイメージ一覧:"
docker images | grep $DOCKER_REPO