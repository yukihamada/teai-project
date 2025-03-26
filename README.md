# TeAI - AIによる開発支援プラットフォーム

<div align="center">
  <img src="docs/images/teai-logo.png" alt="TeAI Logo" width="200">
  <h1 align="center">TeAI: AIの手で、コーディングをもっと簡単に</h1>
</div>

## TeAIとは

TeAI（テアイ）は、AIを活用した開発支援プラットフォームです。コーディング、デバッグ、リファクタリングなど、開発者の日常的なタスクをAIがサポートします。TeAIは「手AI」という意味を持ち、AIがあなたの手となって開発をサポートします。

## 主な機能

- **コード生成**: 自然言語での指示からコードを生成
- **デバッグ支援**: エラーの原因を特定し、修正案を提案
- **リファクタリング**: コードの品質向上のための提案と自動修正
- **ドキュメント生成**: コードからドキュメントを自動生成
- **学習支援**: プログラミング学習のためのガイダンスと説明

## クイックスタート

TeAIは、Dockerを使って簡単に起動できます：

```bash
docker pull teai/app:latest

docker run -it --rm \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE=teai/runtime:latest \
    -e LOG_ALL_EVENTS=true \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v ~/.teai-state:/.teai-state \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    --name teai-app \
    teai/app:latest
```

ブラウザで [http://localhost:3000](http://localhost:3000) にアクセスすると、TeAIが起動します！

## デプロイ

TeAIは以下の方法でデプロイできます：

- **ローカル環境**: 上記のDockerコマンドを使用
- **AWS**: 提供されているCloudFormationテンプレートを使用
- **その他のクラウド**: デプロイスクリプトを参照

詳細は [デプロイガイド](docs/deployment.md) を参照してください。

## ドキュメント

TeAIの詳細な使い方や設定方法については、以下のドキュメントを参照してください：

- [ユーザーガイド](docs/user-guide.md)
- [開発者ガイド](docs/developer-guide.md)
- [API リファレンス](docs/api-reference.md)
- [トラブルシューティング](docs/troubleshooting.md)

## コミュニティ

TeAIのコミュニティに参加して、質問したり、フィードバックを提供したり、貢献したりしましょう：

- [GitHub Issues](https://github.com/teai-jp/teai/issues)
- [Discord](https://discord.gg/teai)
- [Twitter](https://twitter.com/teai_jp)

## ライセンス

TeAIはMITライセンスの下で公開されています。詳細は [LICENSE](LICENSE) ファイルを参照してください。

## 謝辞

TeAIは [OpenHands](https://github.com/All-Hands-AI/OpenHands) をベースに開発されています。OpenHandsチームの素晴らしい取り組みに感謝します。