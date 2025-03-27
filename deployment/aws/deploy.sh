#!/bin/bash

# TeAI AWS デプロイスクリプト
# 使用方法: ./deploy.sh [環境名]
# 例: ./deploy.sh dev

# 引数チェック
if [ $# -ne 1 ]; then
  echo "使用方法: $0 [環境名]"
  echo "環境名: dev, test, prod"
  exit 1
fi

# 環境設定
ENV=$1
STACK_NAME="teai-$ENV"
S3_BUCKET="teai-lambda-code-$ENV"
REGION="ap-northeast-1"
DOMAIN_NAME="teai.io"
HOSTED_ZONE_ID="Z1234567890ABC" # Route 53のホストゾーンID
ACM_CERTIFICATE_ARN="arn:aws:acm:us-east-1:123456789012:certificate/abcdef12-3456-7890-abcd-ef1234567890" # ACM証明書ARN

# 環境変数設定
case $ENV in
  "dev")
    NODE_ENV="development"
    API_SUBDOMAIN="dev-api"
    WEBSITE_SUBDOMAIN="dev"
    ;;
  "test")
    NODE_ENV="test"
    API_SUBDOMAIN="test-api"
    WEBSITE_SUBDOMAIN="test"
    ;;
  "prod")
    NODE_ENV="production"
    API_SUBDOMAIN="api"
    WEBSITE_SUBDOMAIN="www"
    ;;
  *)
    echo "無効な環境名: $ENV"
    echo "有効な環境名: dev, test, prod"
    exit 1
    ;;
esac

echo "=== TeAI $ENV 環境へのデプロイを開始します ==="

# S3バケットが存在するか確認し、存在しなければ作成
if ! aws s3 ls "s3://$S3_BUCKET" 2>&1 > /dev/null; then
  echo "S3バケット $S3_BUCKET を作成します..."
  aws s3 mb "s3://$S3_BUCKET" --region $REGION
fi

# Lambda関数のパッケージング
echo "Lambda関数をパッケージングしています..."
cd lambda

# 依存関係をインストール
echo "依存関係をインストールしています..."
npm install

# 環境変数を設定
echo "NODE_ENV=$NODE_ENV" > .env

# Lambda関数をパッケージング
echo "auth.js をパッケージングしています..."
mkdir -p dist
cp auth.js utils.js dist/
cp -r ../config dist/
cd dist
zip -r ../auth.zip .
cd ..

echo "instances.js をパッケージングしています..."
mkdir -p dist
cp instances.js utils.js dist/
cp -r ../config dist/
cd dist
zip -r ../instances.zip .
cd ..

# Lambda関数をS3にアップロード
echo "Lambda関数をS3にアップロードしています..."
aws s3 cp auth.zip "s3://$S3_BUCKET/"
aws s3 cp instances.zip "s3://$S3_BUCKET/"

cd ..

# CloudFormationテンプレートをS3にアップロード
echo "CloudFormationテンプレートをS3にアップロードしています..."
aws s3 cp cloudformation.yaml "s3://$S3_BUCKET/"

# CloudFormationスタックを作成または更新
echo "バックエンドCloudFormationスタックを作成/更新しています..."
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION 2>&1 > /dev/null; then
  # スタックが存在する場合は更新
  echo "既存のスタック $STACK_NAME を更新しています..."
  aws cloudformation update-stack \
    --stack-name $STACK_NAME \
    --template-url "https://$S3_BUCKET.s3.$REGION.amazonaws.com/cloudformation.yaml" \
    --capabilities CAPABILITY_IAM \
    --parameters \
      ParameterKey=Environment,ParameterValue=$ENV \
      ParameterKey=NodeEnv,ParameterValue=$NODE_ENV \
    --region $REGION
else
  # スタックが存在しない場合は作成
  echo "新しいスタック $STACK_NAME を作成しています..."
  aws cloudformation create-stack \
    --stack-name $STACK_NAME \
    --template-url "https://$S3_BUCKET.s3.$REGION.amazonaws.com/cloudformation.yaml" \
    --capabilities CAPABILITY_IAM \
    --parameters \
      ParameterKey=Environment,ParameterValue=$ENV \
      ParameterKey=NodeEnv,ParameterValue=$NODE_ENV \
    --region $REGION
fi

# スタックの作成/更新が完了するまで待機
echo "バックエンドスタックの作成/更新が完了するまで待機しています..."
aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION || \
aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION

# APIのIDを取得
API_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ApiId'].OutputValue" --output text)

# フロントエンドインフラストラクチャを作成または更新
echo "フロントエンドインフラストラクチャを作成/更新しています..."
FRONTEND_STACK_NAME="${STACK_NAME}-frontend"

# CloudFormationテンプレートをS3にアップロード
aws s3 cp frontend-infrastructure.yaml "s3://$S3_BUCKET/"

if aws cloudformation describe-stacks --stack-name $FRONTEND_STACK_NAME --region $REGION 2>&1 > /dev/null; then
  # スタックが存在する場合は更新
  echo "既存のスタック $FRONTEND_STACK_NAME を更新しています..."
  aws cloudformation update-stack \
    --stack-name $FRONTEND_STACK_NAME \
    --template-url "https://$S3_BUCKET.s3.$REGION.amazonaws.com/frontend-infrastructure.yaml" \
    --parameters \
      ParameterKey=Environment,ParameterValue=$ENV \
      ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
      ParameterKey=SubDomain,ParameterValue=$WEBSITE_SUBDOMAIN \
      ParameterKey=HostedZoneId,ParameterValue=$HOSTED_ZONE_ID \
      ParameterKey=AcmCertificateArn,ParameterValue=$ACM_CERTIFICATE_ARN \
    --region $REGION
else
  # スタックが存在しない場合は作成
  echo "新しいスタック $FRONTEND_STACK_NAME を作成しています..."
  aws cloudformation create-stack \
    --stack-name $FRONTEND_STACK_NAME \
    --template-url "https://$S3_BUCKET.s3.$REGION.amazonaws.com/frontend-infrastructure.yaml" \
    --parameters \
      ParameterKey=Environment,ParameterValue=$ENV \
      ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
      ParameterKey=SubDomain,ParameterValue=$WEBSITE_SUBDOMAIN \
      ParameterKey=HostedZoneId,ParameterValue=$HOSTED_ZONE_ID \
      ParameterKey=AcmCertificateArn,ParameterValue=$ACM_CERTIFICATE_ARN \
    --region $REGION
fi

# APIカスタムドメインを作成または更新
echo "APIカスタムドメインを作成/更新しています..."
API_DOMAIN_STACK_NAME="${STACK_NAME}-api-domain"

# CloudFormationテンプレートをS3にアップロード
aws s3 cp api-domain.yaml "s3://$S3_BUCKET/"

if aws cloudformation describe-stacks --stack-name $API_DOMAIN_STACK_NAME --region $REGION 2>&1 > /dev/null; then
  # スタックが存在する場合は更新
  echo "既存のスタック $API_DOMAIN_STACK_NAME を更新しています..."
  aws cloudformation update-stack \
    --stack-name $API_DOMAIN_STACK_NAME \
    --template-url "https://$S3_BUCKET.s3.$REGION.amazonaws.com/api-domain.yaml" \
    --parameters \
      ParameterKey=Environment,ParameterValue=$ENV \
      ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
      ParameterKey=SubDomain,ParameterValue=$API_SUBDOMAIN \
      ParameterKey=HostedZoneId,ParameterValue=$HOSTED_ZONE_ID \
      ParameterKey=AcmCertificateArn,ParameterValue=$ACM_CERTIFICATE_ARN \
      ParameterKey=ApiId,ParameterValue=$API_ID \
      ParameterKey=ApiStageName,ParameterValue=$ENV \
    --region $REGION
else
  # スタックが存在しない場合は作成
  echo "新しいスタック $API_DOMAIN_STACK_NAME を作成しています..."
  aws cloudformation create-stack \
    --stack-name $API_DOMAIN_STACK_NAME \
    --template-url "https://$S3_BUCKET.s3.$REGION.amazonaws.com/api-domain.yaml" \
    --parameters \
      ParameterKey=Environment,ParameterValue=$ENV \
      ParameterKey=DomainName,ParameterValue=$DOMAIN_NAME \
      ParameterKey=SubDomain,ParameterValue=$API_SUBDOMAIN \
      ParameterKey=HostedZoneId,ParameterValue=$HOSTED_ZONE_ID \
      ParameterKey=AcmCertificateArn,ParameterValue=$ACM_CERTIFICATE_ARN \
      ParameterKey=ApiId,ParameterValue=$API_ID \
      ParameterKey=ApiStageName,ParameterValue=$ENV \
    --region $REGION
fi

# すべてのスタックの作成/更新が完了するまで待機
echo "すべてのスタックの作成/更新が完了するまで待機しています..."
aws cloudformation wait stack-update-complete --stack-name $FRONTEND_STACK_NAME --region $REGION || \
aws cloudformation wait stack-create-complete --stack-name $FRONTEND_STACK_NAME --region $REGION

aws cloudformation wait stack-update-complete --stack-name $API_DOMAIN_STACK_NAME --region $REGION || \
aws cloudformation wait stack-create-complete --stack-name $API_DOMAIN_STACK_NAME --region $REGION

# デプロイ結果を表示
if [ $? -eq 0 ]; then
  echo "=== デプロイが成功しました ==="
  
  # バックエンド情報を取得
  USER_POOL_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='UserPoolId'].OutputValue" --output text)
  CLIENT_ID=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='UserPoolClientId'].OutputValue" --output text)
  
  # フロントエンド情報を取得
  WEBSITE_URL=$(aws cloudformation describe-stacks --stack-name $FRONTEND_STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='WebsiteUrl'].OutputValue" --output text)
  CLOUDFRONT_ID=$(aws cloudformation describe-stacks --stack-name $FRONTEND_STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" --output text)
  
  # API情報を取得
  API_URL=$(aws cloudformation describe-stacks --stack-name $API_DOMAIN_STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
  
  echo "=== $ENV 環境のデプロイ情報 ==="
  echo "API URL: $API_URL"
  echo "Website URL: $WEBSITE_URL"
  echo ""
  echo "フロントエンドの設定を更新するには、以下の値を使用してください:"
  echo "API_URL: $API_URL"
  echo "USER_POOL_ID: $USER_POOL_ID"
  echo "CLIENT_ID: $CLIENT_ID"
  echo ""
  echo "CloudFront Distribution ID: $CLOUDFRONT_ID"
  
  # 環境変数をファイルに保存
  echo "環境変数をファイルに保存しています..."
  cat > .env.$ENV << EOF
API_URL=$API_URL
WEBSITE_URL=$WEBSITE_URL
USER_POOL_ID=$USER_POOL_ID
CLIENT_ID=$CLIENT_ID
CLOUDFRONT_ID=$CLOUDFRONT_ID
EOF

  echo "環境変数が .env.$ENV ファイルに保存されました"
else
  echo "=== デプロイに失敗しました ==="
  echo "CloudFormationスタックのイベントを確認してください:"
  echo "aws cloudformation describe-stack-events --stack-name $STACK_NAME --region $REGION"
  echo "aws cloudformation describe-stack-events --stack-name $FRONTEND_STACK_NAME --region $REGION"
  echo "aws cloudformation describe-stack-events --stack-name $API_DOMAIN_STACK_NAME --region $REGION"
fi