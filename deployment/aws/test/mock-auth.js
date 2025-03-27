// 認証APIのモック

// ユーザープールとクライアントの設定
const USER_POOL_ID = 'ap-northeast-1_wwnIacApg';
const CLIENT_ID = '7m687l847drhsqoo7ai0l10cps';

// モックユーザー
const mockUsers = {
  'test@example.com': {
    email: 'test@example.com',
    password: 'Password123!',
    name: 'Test User',
    sub: 'test-user-id',
    confirmed: true
  }
};

// モックプロファイル
const mockProfiles = {
  'test-user-id': {
    id: 'test-user-id',
    email: 'test@example.com',
    name: 'Test User',
    createdAt: new Date().toISOString()
  }
};

// サインアップ
exports.signUp = async (event) => {
  try {
    const { email, password, name } = JSON.parse(event.body);
    
    // ユーザーが既に存在するかチェック
    if (mockUsers[email]) {
      return {
        statusCode: 400,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'User already exists'
        })
      };
    }
    
    // 新しいユーザーを作成
    const userId = 'test-user-id';
    mockUsers[email] = {
      email,
      password,
      name,
      sub: userId,
      confirmed: true
    };
    
    // プロファイルを作成
    mockProfiles[userId] = {
      id: userId,
      email,
      name,
      createdAt: new Date().toISOString()
    };
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        message: 'User registered successfully',
        userId
      })
    };
  } catch (error) {
    console.error('Error signing up user:', error);
    
    return {
      statusCode: 400,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: false,
        message: error.message
      })
    };
  }
};

// サインイン
exports.signIn = async (event) => {
  try {
    const { email, password } = JSON.parse(event.body);
    
    // ユーザーが存在するかチェック
    if (!mockUsers[email]) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'User does not exist'
        })
      };
    }
    
    // ユーザーが確認済みかチェック
    if (!mockUsers[email].confirmed) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'User is not confirmed'
        })
      };
    }
    
    // パスワードチェック
    if (mockUsers[email].password !== password) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Incorrect password'
        })
      };
    }
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        message: 'User authenticated successfully',
        token: 'dummy-id-token',
        refreshToken: 'dummy-refresh-token',
        expiresIn: 3600
      })
    };
  } catch (error) {
    console.error('Error signing in user:', error);
    
    return {
      statusCode: 401,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: false,
        message: error.message
      })
    };
  }
};

// ユーザー情報取得
exports.getUser = async (event) => {
  try {
    // トークンを取得
    const token = event.headers.Authorization;
    
    if (!token) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'No token provided'
        })
      };
    }
    
    // トークンを検証（モックなので常に成功）
    const userId = 'test-user-id';
    const user = mockProfiles[userId];
    
    if (!user) {
      return {
        statusCode: 404,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'User not found'
        })
      };
    }
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        user
      })
    };
  } catch (error) {
    console.error('Error getting user:', error);
    
    return {
      statusCode: 401,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: false,
        message: error.message
      })
    };
  }
};

// CORS対応
exports.options = async (event) => {
  return {
    statusCode: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
      'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
      'Access-Control-Allow-Credentials': true
    },
    body: JSON.stringify({})
  };
};

// Lambda関数のハンドラー
exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event));
  
  // パスとメソッドに基づいて適切な関数を呼び出す
  const path = event.path || '';
  const method = event.httpMethod || event.requestContext?.http?.method || 'GET';
  
  if (method === 'OPTIONS') {
    return await exports.options(event);
  }
  
  if (path.endsWith('/auth/signup') && method === 'POST') {
    return await exports.signUp(event);
  }
  
  if (path.endsWith('/auth/signin') && method === 'POST') {
    return await exports.signIn(event);
  }
  
  if (path.endsWith('/auth/user') && method === 'GET') {
    return await exports.getUser(event);
  }
  
  return {
    statusCode: 404,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Credentials': true
    },
    body: JSON.stringify({
      success: false,
      message: 'Not Found'
    })
  };
};