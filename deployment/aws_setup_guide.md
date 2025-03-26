# TeAI AWS設定ガイド

## 1. IAMユーザーの作成

1. AWSマネジメントコンソールにログインします。
2. IAMサービスに移動します。
3. 「ユーザー」→「ユーザーを作成」をクリックします。
4. ユーザー名に「teai-service」と入力します。
5. アクセスキーの作成を選択し、「次へ」をクリックします。
6. 「ポリシーを直接アタッチする」を選択し、以下のポリシーを検索して選択します：
   - AmazonSESFullAccess
   - AmazonRoute53FullAccess
7. 「次へ」をクリックし、設定を確認して「ユーザーの作成」をクリックします。
8. 作成されたアクセスキーIDとシークレットアクセスキーをメモします。

## 2. Amazon SESの設定

1. Amazon SESサービスに移動します。
2. 「Verified identities」→「Create identity」をクリックします。
3. 「Domain」を選択し、「teai.io」と入力します。
4. 「Verify this domain for sending email」にチェックを入れます。
5. 「Create identity」をクリックします。
6. 表示されたDNSレコードをRoute 53に追加します。

## 3. Route 53の設定

1. Route 53サービスに移動します。
2. 「ホストゾーン」→「ホストゾーンの作成」をクリックします。
3. ドメイン名に「teai.io」と入力し、「ホストゾーンの作成」をクリックします。
4. 作成されたホストゾーンを選択し、「レコードの作成」をクリックします。
5. 以下のレコードを作成します：
   - 名前: teai.io
   - タイプ: A
   - 値: 54.250.147.206（EC2インスタンスのパブリックIPアドレス）
   - TTL: 300
6. 「レコードの作成」をクリックします。
7. 同様に、ワイルドカードレコードを作成します：
   - 名前: *.teai.io
   - タイプ: A
   - 値: 54.250.147.206（EC2インスタンスのパブリックIPアドレス）
   - TTL: 300
8. 「レコードの作成」をクリックします。
9. SESの検証用DNSレコードも追加します。

## 4. EC2インスタンスの設定

1. EC2インスタンスにSSH接続します。
2. AWSの認証情報を設定します：

```bash
sudo mkdir -p /root/.aws
sudo bash -c 'cat > /root/.aws/credentials << EOF
[default]
aws_access_key_id = YOUR_ACCESS_KEY_ID
aws_secret_access_key = YOUR_SECRET_ACCESS_KEY
EOF'
sudo bash -c 'cat > /root/.aws/config << EOF
[default]
region = ap-northeast-1
EOF'
sudo chmod 600 /root/.aws/credentials
sudo chmod 600 /root/.aws/config
```

3. バックエンドサービスの設定ファイルを編集します：

```bash
sudo vi /usr/local/bin/teai_backend.py
```

4. 以下の設定を更新します：
   - `BASE_URL = 'https://teai.io'`
   - `EMAIL_FROM = 'noreply@teai.io'`
   - `AWS_REGION = 'ap-northeast-1'`

5. バックエンドサービスを再起動します：

```bash
sudo systemctl restart teai-backend
```

## 5. Let's Encryptの設定

1. EC2インスタンスにSSH接続します。
2. Certbotを使用してSSL証明書を取得します：

```bash
sudo certbot --nginx -d teai.io -d *.teai.io --agree-tos --email admin@teai.io --non-interactive
```

3. 証明書の自動更新を確認します：

```bash
sudo certbot renew --dry-run
```

## 6. 動作確認

1. ブラウザで「https://teai.io」にアクセスします。
2. 新規ユーザー登録を行い、確認メールが送信されることを確認します。
3. 確認メールのリンクをクリックして、メール認証が完了することを確認します。
4. ログインして、ユーザー専用のサブドメインにアクセスできることを確認します。
5. 管理者アカウント（admin/admin123）でログインし、管理者ダッシュボードにアクセスできることを確認します。

## 注意事項

- 本番環境では、管理者アカウントのパスワードを強力なものに変更してください。
- AWSの認証情報は厳重に管理し、必要最小限の権限のみを付与してください。
- Let's Encryptの証明書は90日ごとに更新が必要です。自動更新が正しく設定されていることを確認してください。
- ドメインの所有権確認が完了するまで、SESからのメール送信が制限される場合があります。