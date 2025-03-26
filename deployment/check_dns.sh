#!/bin/bash

# DNSの伝播を確認するスクリプト

echo "DNSの伝播を確認しています..."
echo "ドメイン: teai.io"
echo "期待するIPアドレス: 54.250.147.206"
echo ""

# 現在のネームサーバーを確認
echo "現在のネームサーバー:"
aws route53domains get-domain-detail --region us-east-1 --domain-name teai.io --query "Nameservers[].Name" --output text

echo ""
echo "DNSの伝播状況:"

# 複数のDNSサーバーで確認
echo "Google DNS (8.8.8.8):"
dig @8.8.8.8 teai.io +short

echo "Cloudflare DNS (1.1.1.1):"
dig @1.1.1.1 teai.io +short

echo "OpenDNS (208.67.222.222):"
dig @208.67.222.222 teai.io +short

echo "Quad9 (9.9.9.9):"
dig @9.9.9.9 teai.io +short

echo ""
echo "Route 53のネームサーバーでの確認:"
for ns in $(aws route53 get-hosted-zone --id Z07715391N7YX9WETYO74 --query "DelegationSet.NameServers" --output text); do
  echo "$ns:"
  dig @$ns teai.io +short
done

echo ""
echo "DNSの伝播が完了したら、以下のコマンドでLet's Encrypt証明書を取得できます:"
echo "ssh -i ~/.ssh/teai-key.pem -o StrictHostKeyChecking=no ec2-user@54.250.147.206 \"bash /home/ec2-user/get_certificate.sh\""