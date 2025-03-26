# TeAI デプロイガイド

このガイドでは、TeAIをAWS上にデプロイする手順を説明します。

## 前提条件

- AWS CLIがインストールされ、設定済みであること
- AWS アカウントに以下のサービスへのアクセス権限があること:
  - EC2
  - Route 53
  - CloudFormation
  - IAM

## デプロイ手順

### 1. キーペアの作成

まず、EC2インスタンスにSSH接続するためのキーペアを作成します。

```bash
./create_key_pair.sh
```

このスクリプトは、`teai-key`という名前のキーペアを作成し、`~/.ssh/teai-key.pem`に保存します。

### 2. ドメインの設定

次に、TeAIで使用するドメイン（teai.io）を設定します。

```bash
./setup_domain.sh
```

このスクリプトは以下の処理を行います：

1. ドメインが登録済みかチェック
2. 未登録の場合、ドメインを登録
3. ホストゾーンの作成または取得
4. CloudFormationテンプレートのデプロイ

### 3. デプロイの確認

CloudFormationスタックのデプロイが完了したら、以下のURLでTeAIにアクセスできます：

- メインサイト: https://teai.io
- サブドメイン例: https://myteam.teai.io

### 4. SSL証明書の設定

デプロイ後、EC2インスタンスにSSH接続して、Let's Encryptの証明書を取得します：

```bash
ssh -i ~/.ssh/teai-key.pem ec2-user@<EC2インスタンスのパブリックIP>
sudo certbot --nginx -d teai.io -d *.teai.io
```

## トラブルシューティング

### ドメイン登録に関する問題

ドメイン登録に問題がある場合は、AWS Route 53コンソールで登録状況を確認してください。

### CloudFormationスタックのデプロイに失敗した場合

CloudFormationコンソールでスタックのイベントを確認し、エラーの原因を特定してください。

### SSL証明書の取得に失敗した場合

Let's Encryptのワイルドカード証明書を取得するには、DNSチャレンジが必要です。以下のコマンドを試してください：

```bash
sudo certbot certonly --manual --preferred-challenges dns -d teai.io -d *.teai.io
```

指示に従って、DNSレコードを追加してください。

## カスタマイズ

### インスタンスタイプの変更

より大きなインスタンスタイプを使用する場合は、`cloudformation.yaml`の`InstanceType`パラメータを変更してください。

### ボリュームサイズの変更

ディスク容量を増やす場合は、`cloudformation.yaml`の`VolumeSize`パラメータを変更してください。

## メンテナンス

### インスタンスの更新

新しいバージョンのTeAIをデプロイする場合は、EC2インスタンスにSSH接続して以下のコマンドを実行してください：

```bash
ssh -i ~/.ssh/teai-key.pem ec2-user@<EC2インスタンスのパブリックIP>
sudo docker pull teai/app:latest
sudo docker pull teai/runtime:latest
sudo docker stop teai-app
sudo docker run -d --rm \
  -e SANDBOX_RUNTIME_CONTAINER_IMAGE=teai/runtime:latest \
  -e LOG_ALL_EVENTS=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /root/.teai-state:/.teai-state \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  --name teai-app \
  teai/app:latest
```

### バックアップ

定期的にデータベースをバックアップすることをお勧めします：

```bash
ssh -i ~/.ssh/teai-key.pem ec2-user@<EC2インスタンスのパブリックIP>
sudo cp /var/lib/teai/teai.db /var/lib/teai/teai.db.backup
```