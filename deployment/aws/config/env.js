/**
 * 環境設定ファイル
 * 
 * このファイルは環境ごとの設定を管理します。
 * NODE_ENV環境変数に基づいて適切な設定を読み込みます。
 */

// 共通設定
const commonConfig = {
  region: 'ap-northeast-1',
  tables: {
    profiles: 'teai-profiles',
    instances: 'teai-instances'
  }
};

// 開発環境設定
const devConfig = {
  ...commonConfig,
  cognito: {
    userPoolId: 'ap-northeast-1_wwnIacApg',
    clientId: '7m687l847drhsqoo7ai0l10cps'
  },
  api: {
    url: 'https://dev-api.teai.io'
  },
  ec2: {
    defaultImageId: 'ami-0d52744d6551d851e', // Amazon Linux 2 AMI
    defaultInstanceType: 't3a.large'
  },
  cors: {
    allowOrigin: '*'
  }
};

// テスト環境設定
const testConfig = {
  ...commonConfig,
  cognito: {
    userPoolId: 'ap-northeast-1_testUserPool',
    clientId: 'testClientId'
  },
  api: {
    url: 'https://test-api.teai.io'
  },
  ec2: {
    defaultImageId: 'ami-0d52744d6551d851e', // Amazon Linux 2 AMI
    defaultInstanceType: 't3a.small' // テスト環境ではより小さいインスタンスを使用
  },
  cors: {
    allowOrigin: 'https://test.teai.io'
  }
};

// 本番環境設定
const prodConfig = {
  ...commonConfig,
  cognito: {
    userPoolId: 'ap-northeast-1_prodUserPool',
    clientId: 'prodClientId'
  },
  api: {
    url: 'https://api.teai.io'
  },
  ec2: {
    defaultImageId: 'ami-0d52744d6551d851e', // Amazon Linux 2 AMI
    defaultInstanceType: 't3a.large'
  },
  cors: {
    allowOrigin: 'https://teai.io'
  }
};

// 環境に基づいて設定を選択
let config;
switch (process.env.NODE_ENV) {
  case 'production':
    config = prodConfig;
    break;
  case 'test':
    config = testConfig;
    break;
  default:
    config = devConfig;
}

module.exports = config;