#!/bin/bash
# TeAI.ioドメインのセットアップスクリプト

# 設定
DOMAIN="teai.io"
REGION="ap-northeast-1"

# ドメインが登録済みかチェック
echo "ドメイン $DOMAIN の登録状況を確認しています..."
DOMAIN_CHECK=$(aws route53domains get-domain-detail --region us-east-1 --domain-name "$DOMAIN" 2>&1)

if [[ $DOMAIN_CHECK == *"DomainNotFound"* ]]; then
    echo "ドメイン $DOMAIN は登録されていません。登録を開始します..."
    
    # ドメイン登録の連絡先情報
    cat > contact_details.json << EOF
{
    "FirstName": "TeAI",
    "LastName": "Admin",
    "ContactType": "PERSON",
    "OrganizationName": "TeAI Inc.",
    "AddressLine1": "123 AI Street",
    "City": "Tokyo",
    "State": "Tokyo",
    "CountryCode": "JP",
    "ZipCode": "100-0001",
    "PhoneNumber": "+81.123456789",
    "Email": "admin@teai.io"
}
EOF

    # ドメイン登録
    aws route53domains register-domain --region us-east-1 \
        --domain-name "$DOMAIN" \
        --duration-in-years 1 \
        --auto-renew \
        --admin-contact file://contact_details.json \
        --registrant-contact file://contact_details.json \
        --tech-contact file://contact_details.json \
        --privacy-protect-admin-contact \
        --privacy-protect-registrant-contact \
        --privacy-protect-tech-contact
    
    echo "ドメイン登録リクエストを送信しました。登録完了までしばらくお待ちください..."
    echo "登録状況は AWS Route 53 コンソールで確認できます。"
else
    echo "ドメイン $DOMAIN は既に登録されています。"
fi

# ホストゾーンの作成または取得
echo "ホストゾーンを確認しています..."
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name --dns-name "$DOMAIN." --max-items 1 --query 'HostedZones[0].Id' --output text)

if [[ $HOSTED_ZONE_ID == "None" || -z "$HOSTED_ZONE_ID" ]]; then
    echo "ホストゾーンが見つかりません。新しいホストゾーンを作成します..."
    HOSTED_ZONE_ID=$(aws route53 create-hosted-zone --name "$DOMAIN" --caller-reference "$(date +%s)" --query 'HostedZone.Id' --output text)
    echo "ホストゾーン $HOSTED_ZONE_ID を作成しました。"
else
    echo "既存のホストゾーン $HOSTED_ZONE_ID を使用します。"
fi

# ホストゾーンIDからプレフィックスを削除
HOSTED_ZONE_ID=${HOSTED_ZONE_ID##*/}
echo "ホストゾーンID: $HOSTED_ZONE_ID"

# CloudFormationテンプレートのデプロイ
echo "CloudFormationスタックをデプロイします..."
aws cloudformation create-stack \
    --stack-name TeAI-Stack \
    --template-body file://cloudformation.yaml \
    --parameters \
        ParameterKey=InstanceType,ParameterValue=t3a.large \
        ParameterKey=KeyName,ParameterValue=teai-key \
        ParameterKey=VolumeSize,ParameterValue=30 \
        ParameterKey=DomainName,ParameterValue="$DOMAIN" \
        ParameterKey=HostedZoneId,ParameterValue="$HOSTED_ZONE_ID" \
    --capabilities CAPABILITY_IAM \
    --region "$REGION"

echo "CloudFormationスタックのデプロイを開始しました。"
echo "スタックの作成状況は AWS CloudFormation コンソールで確認できます。"
echo "スタックの作成が完了したら、以下のURLでTeAIにアクセスできます："
echo "https://$DOMAIN"
echo "サブドメイン例: https://myteam.$DOMAIN"