# TeAI AWS デプロイガイド

このガイドでは、TeAIをAWSにデプロイする手順を説明します。

## 環境

TeAIは以下の3つの環境をサポートしています：

1. **開発環境 (dev)** - 開発者が新機能を開発・テストするための環境
2. **テスト環境 (test)** - QAチームがテストを行うための環境
3. **本番環境 (prod)** - エンドユーザーが使用する環境

各環境は完全に分離されており、それぞれ独自のリソース（Cognito、DynamoDB、Lambda、API Gateway）を持ちます。

## 前提条件

- AWS CLIがインストールされていること
- AWS認証情報が設定されていること
- Node.jsとnpmがインストールされていること
- デプロイ権限を持つIAMユーザーまたはロールが設定されていること

## デプロイ手順

### 1. デプロイスクリプトの実行

```bash
# デプロイスクリプトに実行権限を付与
chmod +x deploy.sh

# 開発環境にデプロイ
./deploy.sh dev

# テスト環境にデプロイ
./deploy.sh test

# 本番環境にデプロイ
./deploy.sh prod
```

デプロイスクリプトは以下の処理を行います：

1. Lambda関数のパッケージング
2. S3バケットの作成（存在しない場合）
3. Lambda関数とCloudFormationテンプレートのS3へのアップロード
4. CloudFormationスタックの作成または更新
5. デプロイ結果の表示

### 2. フロントエンドの設定更新

デプロイが完了すると、フロントエンドの設定を更新するための情報が表示されます。

```
API URL: https://abcdefghij.execute-api.ap-northeast-1.amazonaws.com/dev
USER_POOL_ID: ap-northeast-1_abcdefghi
CLIENT_ID: abcdefghijklmnopqrstu
```

これらの値を使用して、フロントエンドの設定ファイル `config.js` を更新します。

### 3. フロントエンドのデプロイ

フロントエンドは環境ごとに異なるS3バケットにデプロイします。

```bash
# 開発環境用のフロントエンドをビルド
TEAI_ENV=dev npm run build

# 開発環境にデプロイ
aws s3 sync ./build/ s3://teai-website-dev/ --delete

# テスト環境用のフロントエンドをビルド
TEAI_ENV=test npm run build

# テスト環境にデプロイ
aws s3 sync ./build/ s3://teai-website-test/ --delete

# 本番環境用のフロントエンドをビルド
TEAI_ENV=prod npm run build

# 本番環境にデプロイ
aws s3 sync ./build/ s3://teai-website-prod/ --delete
```

## 環境変数

### バックエンド（Lambda関数）

Lambda関数は以下の環境変数を使用します：

- `NODE_ENV` - Node.js環境（development, test, production）
- `USER_POOL_ID` - Cognito User Pool ID
- `CLIENT_ID` - Cognito User Pool Client ID
- `PROFILES_TABLE` - プロファイルテーブル名
- `INSTANCES_TABLE` - インスタンステーブル名
- `EC2_IMAGE_ID` - EC2インスタンスのAMI ID
- `EC2_INSTANCE_TYPE` - EC2インスタンスタイプ

これらの環境変数はCloudFormationテンプレートで設定されます。

### フロントエンド

フロントエンドは以下の環境変数を使用します：

- `TEAI_ENV` - 環境名（dev, test, prod）

この環境変数はビルド時に設定され、適切な設定ファイルを読み込むために使用されます。

## リソース命名規則

すべてのリソースは環境名をサフィックスとして持ちます：

- CloudFormationスタック: `teai-{env}`
- Cognito User Pool: `teai-users-{env}`
- Cognito User Pool Client: `teai-client-{env}`
- DynamoDBテーブル: `teai-profiles-{env}`, `teai-instances-{env}`
- Lambda関数: `teai-auth-{env}`, `teai-instances-{env}`
- API Gateway: `TeAI API {env}`
- S3バケット: `teai-lambda-code-{env}`, `teai-website-{env}`

## セキュリティ考慮事項

- 本番環境のデプロイは、適切な権限を持つ担当者のみが実行してください
- 本番環境の認証情報は安全に管理してください
- 環境間でのデータ移行は慎重に行ってください
- 本番環境へのデプロイ前に、必ずテスト環境でテストを行ってください

## トラブルシューティング

### デプロイに失敗した場合

CloudFormationスタックのイベントを確認してください：

```bash
aws cloudformation describe-stack-events --stack-name teai-dev --region ap-northeast-1
```

### Lambda関数のログを確認

```bash
aws logs filter-log-events --log-group-name /aws/lambda/teai-auth-dev --region ap-northeast-1
aws logs filter-log-events --log-group-name /aws/lambda/teai-instances-dev --region ap-northeast-1
```

### API Gatewayのログを確認

```bash
aws logs filter-log-events --log-group-name API-Gateway-Execution-Logs_abcdefghij/dev --region ap-northeast-1
```