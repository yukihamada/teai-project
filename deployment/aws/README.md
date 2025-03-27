# TeAI AWS デプロイガイド

このガイドでは、TeAIをAWSにデプロイする手順を説明します。

## 前提条件

- AWS CLIがインストールされていること
- AWS認証情報が設定されていること
- Node.jsとnpmがインストールされていること

## デプロイ手順

### 1. Lambda関数のパッケージング

```bash
# Lambda関数のディレクトリに移動
cd deployment/aws/lambda/package

# 依存関係をインストール
npm install

# auth.jsをコピー
cp ../auth.js .

# instances.jsをコピー
cp ../instances.js .

# パッケージング
zip -r auth.zip auth.js node_modules
zip -r instances.zip instances.js node_modules

# S3バケットを作成
aws s3 mb s3://teai-lambda-code

# Lambda関数をアップロード
aws s3 cp auth.zip s3://teai-lambda-code/
aws s3 cp instances.zip s3://teai-lambda-code/
```

### 2. CloudFormationスタックのデプロイ

```bash
# CloudFormationスタックを作成
aws cloudformation create-stack \
  --stack-name teai-stack \
  --template-body file://deployment/aws/cloudformation.yaml \
  --capabilities CAPABILITY_IAM
```

### 3. API GatewayのエンドポイントURLを取得

```bash
# CloudFormationスタックの出力を取得
aws cloudformation describe-stacks \
  --stack-name teai-stack \
  --query "Stacks[0].Outputs[?OutputKey=='ApiEndpoint'].OutputValue" \
  --output text
```

### 4. フロントエンドの設定を更新

`deployment/aws/frontend/aws-client.js`ファイルを開き、以下の設定を更新します：

```javascript
const API_URL = 'https://[API_ID].execute-api.ap-northeast-1.amazonaws.com/prod';
```

上記の`[API_ID]`を、ステップ3で取得したAPI GatewayのエンドポイントURLに置き換えます。

### 5. フロントエンドのデプロイ

```bash
# S3バケットを作成
aws s3 mb s3://teai-website

# バケットを静的ウェブサイトとして設定
aws s3 website s3://teai-website --index-document index.html --error-document error.html

# フロントエンドファイルをアップロード
aws s3 cp deployment/aws/frontend/ s3://teai-website/ --recursive
aws s3 cp /var/www/teai.io/ s3://teai-website/ --recursive

# CloudFrontディストリビューションを作成
aws cloudfront create-distribution \
  --origin-domain-name teai-website.s3.amazonaws.com \
  --default-root-object index.html
```

### 6. DNSの設定

CloudFrontディストリビューションのドメイン名を取得し、Route 53でDNSレコードを設定します。

```bash
# CloudFrontディストリビューションのドメイン名を取得
aws cloudfront list-distributions \
  --query "DistributionList.Items[?Origins.Items[0].DomainName=='teai-website.s3.amazonaws.com'].DomainName" \
  --output text

# Route 53でDNSレコードを設定
aws route53 change-resource-record-sets \
  --hosted-zone-id [HOSTED_ZONE_ID] \
  --change-batch '{
    "Changes": [
      {
        "Action": "UPSERT",
        "ResourceRecordSet": {
          "Name": "teai.io",
          "Type": "A",
          "AliasTarget": {
            "HostedZoneId": "Z2FDTNDATAQYW2",
            "DNSName": "[CLOUDFRONT_DOMAIN]",
            "EvaluateTargetHealth": false
          }
        }
      }
    ]
  }'
```

## トラブルシューティング

### Lambda関数のログを確認

```bash
# Lambda関数のログを確認
aws logs filter-log-events \
  --log-group-name /aws/lambda/teai-auth \
  --start-time $(date -d "1 hour ago" +%s000) \
  --end-time $(date +%s000)

aws logs filter-log-events \
  --log-group-name /aws/lambda/teai-instances \
  --start-time $(date -d "1 hour ago" +%s000) \
  --end-time $(date +%s000)
```

### API Gatewayのログを確認

```bash
# API Gatewayのログを有効化
aws apigateway update-stage \
  --rest-api-id [API_ID] \
  --stage-name prod \
  --patch-operations op=replace,path=/accessLogSettings/destinationArn,value=arn:aws:logs:ap-northeast-1:495350830663:log-group:api-gateway-logs

# API Gatewayのログを確認
aws logs filter-log-events \
  --log-group-name api-gateway-logs \
  --start-time $(date -d "1 hour ago" +%s000) \
  --end-time $(date +%s000)
```

### CloudFormationスタックの削除

```bash
# CloudFormationスタックを削除
aws cloudformation delete-stack \
  --stack-name teai-stack
```