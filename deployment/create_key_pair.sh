#!/bin/bash
# TeAI用のEC2キーペアを作成するスクリプト

# 設定
KEY_NAME="teai-key"
REGION="ap-northeast-1"
KEY_PATH="$HOME/.ssh/${KEY_NAME}.pem"

# キーペアが既に存在するか確認
echo "キーペア $KEY_NAME の存在を確認しています..."
KEY_CHECK=$(aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" 2>&1)

if [[ $KEY_CHECK == *"InvalidKeyPair.NotFound"* ]]; then
    echo "キーペア $KEY_NAME は存在しません。新しいキーペアを作成します..."
    
    # キーペアの作成
    aws ec2 create-key-pair --key-name "$KEY_NAME" --query 'KeyMaterial' --output text --region "$REGION" > "$KEY_PATH"
    
    if [ $? -eq 0 ]; then
        chmod 400 "$KEY_PATH"
        echo "キーペア $KEY_NAME を作成し、$KEY_PATH に保存しました。"
    else
        echo "キーペアの作成に失敗しました。"
        exit 1
    fi
else
    echo "キーペア $KEY_NAME は既に存在します。"
    
    # キーファイルが存在するか確認
    if [ ! -f "$KEY_PATH" ]; then
        echo "警告: キーペアは存在しますが、キーファイル $KEY_PATH が見つかりません。"
        echo "既存のキーペアを削除して新しいキーペアを作成しますか？ (y/n)"
        read ANSWER
        
        if [[ $ANSWER == "y" ]]; then
            echo "既存のキーペアを削除します..."
            aws ec2 delete-key-pair --key-name "$KEY_NAME" --region "$REGION"
            
            echo "新しいキーペアを作成します..."
            aws ec2 create-key-pair --key-name "$KEY_NAME" --query 'KeyMaterial' --output text --region "$REGION" > "$KEY_PATH"
            
            if [ $? -eq 0 ]; then
                chmod 400 "$KEY_PATH"
                echo "キーペア $KEY_NAME を作成し、$KEY_PATH に保存しました。"
            else
                echo "キーペアの作成に失敗しました。"
                exit 1
            fi
        else
            echo "既存のキーペアを使用します。キーファイルが必要な場合は手動で取得してください。"
        fi
    else
        echo "キーファイル $KEY_PATH が存在します。"
    fi
fi

echo "キーペアの設定が完了しました。"