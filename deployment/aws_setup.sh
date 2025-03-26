#!/bin/bash

# === CONFIG ==============================
REGION="ap-northeast-1"
KEY_NAME="teai-key"
KEY_PATH="$HOME/.ssh/${KEY_NAME}.pem"
SECURITY_GROUP="teai-sg"
INSTANCE_TAG="TeAI"
INSTANCE_TYPE="t3a.large"  # 大きめに変更
VOLUME_SIZE=30  # ディスク30GB
# 最新 Amazon Linux 2 AMI を取得
AMI_ID=$(aws ec2 describe-images \
  --owners amazon \
  --filters "Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2" "Name=state,Values=available" \
  --query 'Images | sort_by(@, &CreationDate)[-1].ImageId' \
  --output text --region "$REGION")
# =========================================

print_header() {
  clear
  echo -e "\033[1;34m"
  echo "╔════════════════════════════════════════════╗"
  echo "║     🧠 TeAI EC2 Manager                   ║"
  echo "╠════════════════════════════════════════════╣"
  echo -e "\033[0m"
}

print_menu() {
  print_header
  echo -e "   1️⃣  一覧表示（稼働中）"
  echo -e "   2️⃣  新しいインスタンスを起動"
  echo -e "   3️⃣  インスタンスを削除"
  echo -e "   4️⃣  ログを確認"
  echo -e "   5️⃣  終了"
  echo -ne "\n📎 選択してください: "
}

list_instances_raw() {
  aws ec2 describe-instances --region "$REGION" \
    --filters "Name=tag:Name,Values=$INSTANCE_TAG" \
    --query "Reservations[*].Instances[*].{ID:InstanceId,IP:PublicIpAddress,State:State.Name}" \
    --output json
}

list_instances() {
  print_header
  echo "📋 稼働中のインスタンス一覧:"
  INSTANCES=$(list_instances_raw)
  echo "$INSTANCES" | jq -r 'flatten | to_entries[] | "[\(.key)] ID: \(.value.ID) | IP: \(.value.IP) | State: \(.value.State)"'
  echo
}

select_instance() {
  INSTANCES=$(list_instances_raw)
  IDS=($(echo "$INSTANCES" | jq -r 'flatten | .[].ID'))
  IPS=($(echo "$INSTANCES" | jq -r 'flatten | .[].IP'))
  count=${#IDS[@]}

  for i in $(seq 0 $((count - 1))); do
    echo "[$i] ${IDS[$i]} (${IPS[$i]})"
  done
  echo -ne "\n選択番号を入力: "
  read INDEX
  SELECTED_ID=${IDS[$INDEX]}
  SELECTED_IP=${IPS[$INDEX]}
}

create_key_and_sg() {
  if [ ! -f "$KEY_PATH" ]; then
    aws ec2 create-key-pair --key-name "$KEY_NAME" \
      --query 'KeyMaterial' --output text --region "$REGION" > "$KEY_PATH"
    chmod 400 "$KEY_PATH"
  fi

  SG_ID=$(aws ec2 describe-security-groups --region "$REGION" \
    --filters Name=group-name,Values="$SECURITY_GROUP" \
    --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null)

  if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
    SG_ID=$(aws ec2 create-security-group \
      --group-name "$SECURITY_GROUP" \
      --description "TeAI SG" --region "$REGION" \
      --query 'GroupId' --output text)

    aws ec2 authorize-security-group-ingress \
      --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 --region "$REGION"

    aws ec2 authorize-security-group-ingress \
      --group-id "$SG_ID" --protocol tcp --port 3000 --cidr 0.0.0.0/0 --region "$REGION"
  fi
}

wait_for_ssh() {
  for i in {1..30}; do
    nc -z -w 3 "$1" 22 && return
    sleep 5
  done
  echo "❌ SSHタイムアウト"
}

setup_script() {
  cat << 'EOF' > teai_setup.sh
#!/bin/bash
set -e
exec > >(tee -a ~/setup.log) 2>&1

IMAGE_TAG="latest"
RUNTIME_IMAGE="teai/runtime:${IMAGE_TAG}"
APP_IMAGE="teai/app:${IMAGE_TAG}"

# 一時的にOpenHandsのイメージを使用
RUNTIME_IMAGE="docker.all-hands.dev/all-hands-ai/runtime:0.30-nikolaik"
APP_IMAGE="docker.all-hands.dev/all-hands-ai/openhands:0.30"

sudo amazon-linux-extras install docker -y
sudo systemctl enable docker
sudo systemctl start docker

sudo docker pull $RUNTIME_IMAGE
sudo docker pull $APP_IMAGE

sudo docker run -d --rm \
  -e SANDBOX_RUNTIME_CONTAINER_IMAGE=$RUNTIME_IMAGE \
  -e LOG_ALL_EVENTS=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.teai-state:/.teai-state \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  --name teai-app \
  $APP_IMAGE
EOF
}

deploy_instance() {
  create_key_and_sg
  setup_script
  echo -ne "🆕 起動する台数: "
  read COUNT

  for i in $(seq 1 $COUNT); do
    echo "🚀 起動中（$i/$COUNT）..."
    INSTANCE_ID=$(aws ec2 run-instances \
      --image-id "$AMI_ID" \
      --count 1 --instance-type "$INSTANCE_TYPE" \
      --key-name "$KEY_NAME" \
      --security-groups "$SECURITY_GROUP" \
      --region "$REGION" \
      --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":30}}]' \
      --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_TAG}]" \
      --query 'Instances[0].InstanceId' --output text)

    aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
    PUBLIC_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$REGION" \
      --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

    wait_for_ssh "$PUBLIC_IP"
    scp -o StrictHostKeyChecking=no -i "$KEY_PATH" teai_setup.sh ec2-user@"$PUBLIC_IP":~/setup.sh
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@"$PUBLIC_IP" "bash ~/setup.sh"

    echo -e "\n🎉 起動完了: http://$PUBLIC_IP:3000"
  done
  echo -ne "\n🔙 Enterで戻ります..." && read
}

terminate_instances() {
  list_instances
  echo -ne "\n🗑️ 削除する番号（スペース区切り）: "
  read NUMBERS
  INSTANCES=$(list_instances_raw)
  IDS=($(echo "$INSTANCES" | jq -r 'flatten | .[].ID'))
  for n in $NUMBERS; do
    SELECTED_IDS+=" ${IDS[$n]}"
  done
  aws ec2 terminate-instances --instance-ids $SELECTED_IDS --region "$REGION"
  echo "✅ 削除しました"
  echo -ne "\n🔙 Enterで戻ります..." && read
}

show_logs() {
  list_instances
  echo -ne "\n🔍 ログ確認する番号を入力: "
  read INDEX
  INSTANCES=$(list_instances_raw)
  ID=$(echo "$INSTANCES" | jq -r "flatten | .[$INDEX].ID")
  IP=$(echo "$INSTANCES" | jq -r "flatten | .[$INDEX].IP")

  ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@"$IP" "
    echo '==== 📝 setup.log ===='
    cat ~/setup.log 2>/dev/null || echo '[ログなし]'
    echo ''
    echo '==== 🐳 docker logs ===='
    sudo docker logs teai-app 2>/dev/null || echo '[コンテナ未起動]'
    echo ''"

  echo -ne "\n🔙 Enterで戻ります..." && read
}

# === Main ===
while true; do
  print_menu
  read CHOICE
  case $CHOICE in
    1) list_instances ;;
    2) deploy_instance ;;
    3) terminate_instances ;;
    4) show_logs ;;
    5) echo "👋 終了します！" && exit 0 ;;
    *) echo "❓ 無効な選択です" && sleep 1 ;;
  esac
done