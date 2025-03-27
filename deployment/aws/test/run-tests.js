// テスト実行スクリプト

// モックを適用
// AWS SDKをモックに置き換え
const mockAWS = require('./mock');
const path = require('path');

// モジュールキャッシュからaws-sdkを削除
delete require.cache[require.resolve('aws-sdk')];

// aws-sdkをモックに置き換え
require.cache[require.resolve('aws-sdk')] = {
  exports: mockAWS
};

// テストを実行
async function runTests() {
  console.log('=== TeAI APIテスト開始 ===\n');
  
  try {
    // 認証APIテスト
    await require('./test-auth');
    
    // インスタンス管理APIテスト
    await require('./test-instances');
    
    console.log('\n=== TeAI APIテスト完了 ===');
  } catch (error) {
    console.error('テスト実行中にエラーが発生しました:', error);
  }
}

// テスト実行
runTests();