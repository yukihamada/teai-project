/**
 * フロントエンド環境設定
 * 
 * このファイルは環境ごとの設定を管理します。
 * 環境変数 TEAI_ENV に基づいて適切な設定を読み込みます。
 */

// 開発環境設定
const devConfig = {
  api: {
    url: 'https://dev-api.teai.io'
  },
  cognito: {
    region: 'ap-northeast-1',
    userPoolId: 'ap-northeast-1_wwnIacApg',
    clientId: '7m687l847drhsqoo7ai0l10cps'
  }
};

// テスト環境設定
const testConfig = {
  api: {
    url: 'https://test-api.teai.io'
  },
  cognito: {
    region: 'ap-northeast-1',
    userPoolId: 'ap-northeast-1_testUserPool',
    clientId: 'testClientId'
  }
};

// 本番環境設定
const prodConfig = {
  api: {
    url: 'https://api.teai.io'
  },
  cognito: {
    region: 'ap-northeast-1',
    userPoolId: 'ap-northeast-1_prodUserPool',
    clientId: 'prodClientId'
  }
};

// 環境に基づいて設定を選択
let config;
const env = window.TEAI_ENV || 'dev';

switch (env) {
  case 'prod':
    config = prodConfig;
    break;
  case 'test':
    config = testConfig;
    break;
  default:
    config = devConfig;
}

// グローバル設定として公開
window.TEAI_CONFIG = config;