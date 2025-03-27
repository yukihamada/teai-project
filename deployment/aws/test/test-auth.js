// 認証APIのテスト

// モックイベント
const signUpEvent = {
  path: '/auth/signup',
  httpMethod: 'POST',
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'Password123!',
    name: 'Test User'
  })
};

const signInEvent = {
  path: '/auth/signin',
  httpMethod: 'POST',
  body: JSON.stringify({
    email: 'test@example.com',
    password: 'Password123!'
  })
};

const getUserEvent = {
  path: '/auth/user',
  httpMethod: 'GET',
  headers: {
    Authorization: 'dummy-id-token'
  }
};

// モック関数をインポート
const authHandler = require('./mock-auth').handler;

// テスト実行
async function runTests() {
  console.log('=== 認証APIテスト開始 ===');
  
  try {
    // サインアップテスト
    console.log('\n--- サインアップテスト ---');
    const signUpResult = await authHandler(signUpEvent);
    console.log('ステータスコード:', signUpResult.statusCode);
    console.log('レスポンス:', signUpResult.body);
    
    // サインインテスト
    console.log('\n--- サインインテスト ---');
    const signInResult = await authHandler(signInEvent);
    console.log('ステータスコード:', signInResult.statusCode);
    console.log('レスポンス:', signInResult.body);
    
    // ユーザー情報取得テスト
    console.log('\n--- ユーザー情報取得テスト ---');
    const getUserResult = await authHandler(getUserEvent);
    console.log('ステータスコード:', getUserResult.statusCode);
    console.log('レスポンス:', getUserResult.body);
    
    console.log('\n=== 認証APIテスト完了 ===');
  } catch (error) {
    console.error('テスト実行中にエラーが発生しました:', error);
  }
}

// テスト実行
runTests();