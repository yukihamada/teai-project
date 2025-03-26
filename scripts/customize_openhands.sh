#!/bin/bash
# OpenHandsのコードをTeAI用にカスタマイズするスクリプト

# 設定
OPENHANDS_REPO="https://github.com/All-Hands-AI/OpenHands.git"
OPENHANDS_DIR="/tmp/openhands"
TEAI_SRC_DIR="$(pwd)/src"

# OpenHandsリポジトリのクローン
echo "OpenHandsリポジトリをクローンしています..."
git clone $OPENHANDS_REPO $OPENHANDS_DIR

# TeAIのソースディレクトリを作成
echo "TeAIのソースディレクトリを準備しています..."
mkdir -p $TEAI_SRC_DIR

# OpenHandsのコードをTeAIディレクトリにコピー
echo "OpenHandsのコードをコピーしています..."
cp -r $OPENHANDS_DIR/* $TEAI_SRC_DIR/

# 不要なファイルを削除
echo "不要なファイルを削除しています..."
rm -rf $TEAI_SRC_DIR/.git
rm -rf $TEAI_SRC_DIR/.github
rm -f $TEAI_SRC_DIR/README.md
rm -f $TEAI_SRC_DIR/LICENSE
rm -f $TEAI_SRC_DIR/CREDITS.md
rm -f $TEAI_SRC_DIR/COMMUNITY.md
rm -f $TEAI_SRC_DIR/CONTRIBUTING.md

# ブランド名の置換
echo "ブランド名を置換しています..."
find $TEAI_SRC_DIR -type f -name "*.py" -o -name "*.md" -o -name "*.html" -o -name "*.js" | xargs sed -i 's/OpenHands/TeAI/g'
find $TEAI_SRC_DIR -type f -name "*.py" -o -name "*.md" -o -name "*.html" -o -name "*.js" | xargs sed -i 's/openhands/teai/g'
find $TEAI_SRC_DIR -type f -name "*.py" -o -name "*.md" -o -name "*.html" -o -name "*.js" | xargs sed -i 's/OPENHANDS/TEAI/g'

# pyproject.tomlの更新
echo "pyproject.tomlを更新しています..."
sed -i 's/name = "openhands"/name = "teai"/g' $TEAI_SRC_DIR/pyproject.toml
sed -i 's/version = ".*"/version = "1.0.0"/g' $TEAI_SRC_DIR/pyproject.toml
sed -i 's/authors = \[.*\]/authors = ["TeAI Team <info@teai.io>"]/g' $TEAI_SRC_DIR/pyproject.toml
sed -i 's|repository = ".*"|repository = "https://github.com/teai-jp/teai"|g' $TEAI_SRC_DIR/pyproject.toml

# ディレクトリ名の変更
echo "ディレクトリ名を変更しています..."
if [ -d "$TEAI_SRC_DIR/openhands" ]; then
    mv $TEAI_SRC_DIR/openhands $TEAI_SRC_DIR/teai
fi

# import文の更新
echo "import文を更新しています..."
find $TEAI_SRC_DIR -type f -name "*.py" | xargs sed -i 's/from openhands/from teai/g'
find $TEAI_SRC_DIR -type f -name "*.py" | xargs sed -i 's/import openhands/import teai/g'

# Dockerfileの更新
echo "Dockerfileを更新しています..."
if [ -f "$TEAI_SRC_DIR/Dockerfile" ]; then
    sed -i 's/LABEL org.opencontainers.image.title="OpenHands"/LABEL org.opencontainers.image.title="TeAI"/g' $TEAI_SRC_DIR/Dockerfile
    sed -i 's/LABEL org.opencontainers.image.description=".*"/LABEL org.opencontainers.image.description="TeAI - AIによる開発支援プラットフォーム"/g' $TEAI_SRC_DIR/Dockerfile
    sed -i 's/LABEL org.opencontainers.image.url=".*"/LABEL org.opencontainers.image.url="https:\/\/teai.io"/g' $TEAI_SRC_DIR/Dockerfile
fi

# 一時ディレクトリの削除
echo "一時ディレクトリを削除しています..."
rm -rf $OPENHANDS_DIR

echo "カスタマイズが完了しました！"
echo "TeAIのソースコードは $TEAI_SRC_DIR に配置されました。"