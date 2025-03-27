const AWS = require('aws-sdk');
const config = require('../config/env');

// リージョン設定
AWS.config.update({ region: config.region });
const cognito = new AWS.CognitoIdentityServiceProvider();
const dynamodb = new AWS.DynamoDB.DocumentClient();

// ユーザープールとクライアントの設定
const USER_POOL_ID = process.env.USER_POOL_ID || config.cognito.userPoolId;
const CLIENT_ID = process.env.CLIENT_ID || config.cognito.clientId;

// サインアップ
exports.signUp = async (event) => {
  try {
    const { email, password, name } = JSON.parse(event.body);
    
    // Cognitoでユーザーを作成
    const params = {
      ClientId: CLIENT_ID,
      Password: password,
      Username: email,
      UserAttributes: [
        {
          Name: 'email',
          Value: email
        },
        {
          Name: 'name',
          Value: name
        }
      ]
    };
    
    const result = await cognito.signUp(params).promise();
    
    // DynamoDBにプロファイルを作成
    await dynamodb.put({
      TableName: 'teai-profiles',
      Item: {
        id: result.UserSub,
        email: email,
        name: name,
        createdAt: new Date().toISOString()
      }
    }).promise();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        message: 'User registered successfully',
        userId: result.UserSub
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
    
    // Cognitoで認証
    const params = {
      AuthFlow: 'USER_PASSWORD_AUTH',
      ClientId: CLIENT_ID,
      AuthParameters: {
        USERNAME: email,
        PASSWORD: password
      }
    };
    
    const result = await cognito.initiateAuth(params).promise();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        message: 'User authenticated successfully',
        token: result.AuthenticationResult.IdToken,
        refreshToken: result.AuthenticationResult.RefreshToken,
        expiresIn: result.AuthenticationResult.ExpiresIn
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
    
    // Cognitoでユーザー情報を取得
    const params = {
      AccessToken: token
    };
    
    const result = await cognito.getUser(params).promise();
    
    // ユーザー属性をオブジェクトに変換
    const userAttributes = {};
    result.UserAttributes.forEach(attr => {
      userAttributes[attr.Name] = attr.Value;
    });
    
    // DynamoDBからプロファイル情報を取得
    const profileResult = await dynamodb.get({
      TableName: 'teai-profiles',
      Key: {
        id: userAttributes.sub
      }
    }).promise();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        user: {
          id: userAttributes.sub,
          email: userAttributes.email,
          name: userAttributes.name,
          ...profileResult.Item
        }
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
      'Access-Control-Allow-Origin': config.cors.allowOrigin,
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