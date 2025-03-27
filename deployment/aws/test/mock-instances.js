// インスタンス管理APIのモック

const { v4: uuidv4 } = require('uuid');

// テーブル名
const INSTANCES_TABLE = 'teai-instances';

// モックインスタンス
const mockInstances = {
  '34ad8b76-f050-4f05-8515-de3b9685c19c': {
    id: '34ad8b76-f050-4f05-8515-de3b9685c19c',
    userId: 'test-user-id',
    name: 'Test Instance',
    instanceType: 't3a.large',
    ec2InstanceId: 'i-12345678901234567',
    ipAddress: '192.168.1.1',
    status: 'running',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString()
  }
};

// モックEC2インスタンス
const mockEC2Instances = {
  'i-12345678901234567': {
    InstanceId: 'i-12345678901234567',
    State: {
      Name: 'running'
    },
    PublicIpAddress: '192.168.1.1',
    PrivateIpAddress: '10.0.0.1'
  }
};

// インスタンス一覧取得
exports.listInstances = async (event) => {
  try {
    // ユーザーIDを取得（認証情報から）
    const userId = event.requestContext.authorizer.claims.sub;
    
    if (!userId) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Unauthorized'
        })
      };
    }
    
    // ユーザーのインスタンス一覧を取得
    const instances = Object.values(mockInstances).filter(instance => instance.userId === userId);
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        instances
      })
    };
  } catch (error) {
    console.error('Error listing instances:', error);
    
    return {
      statusCode: 500,
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

// インスタンス作成
exports.createInstance = async (event) => {
  try {
    // ユーザーIDを取得（認証情報から）
    const userId = event.requestContext.authorizer.claims.sub;
    
    if (!userId) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Unauthorized'
        })
      };
    }
    
    const { name, instanceType } = JSON.parse(event.body);
    
    // 新しいインスタンスを作成
    const instanceId = uuidv4();
    const ec2InstanceId = 'i-' + Math.random().toString(36).substring(2, 15);
    const ipAddress = '192.168.1.' + Math.floor(Math.random() * 255);
    
    // EC2インスタンス情報を保存
    mockEC2Instances[ec2InstanceId] = {
      InstanceId: ec2InstanceId,
      State: {
        Name: 'running'
      },
      PublicIpAddress: ipAddress,
      PrivateIpAddress: '10.0.0.' + Math.floor(Math.random() * 255)
    };
    
    // インスタンス情報を保存
    mockInstances[instanceId] = {
      id: instanceId,
      userId,
      name,
      instanceType: instanceType || 't3a.large',
      ec2InstanceId,
      ipAddress,
      status: 'running',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        instance: mockInstances[instanceId]
      })
    };
  } catch (error) {
    console.error('Error creating instance:', error);
    
    return {
      statusCode: 500,
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

// インスタンス取得
exports.getInstance = async (event) => {
  try {
    // ユーザーIDを取得（認証情報から）
    const userId = event.requestContext.authorizer.claims.sub;
    
    if (!userId) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Unauthorized'
        })
      };
    }
    
    const instanceId = event.pathParameters.id;
    
    // インスタンス情報を取得
    const instance = mockInstances[instanceId];
    
    if (!instance) {
      return {
        statusCode: 404,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Instance not found'
        })
      };
    }
    
    // 権限チェック
    if (instance.userId !== userId) {
      return {
        statusCode: 403,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Forbidden'
        })
      };
    }
    
    // EC2インスタンスの最新情報を取得
    const ec2Instance = mockEC2Instances[instance.ec2InstanceId];
    
    if (ec2Instance) {
      // インスタンス情報を更新
      instance.status = ec2Instance.State.Name;
      instance.ipAddress = ec2Instance.PublicIpAddress || ec2Instance.PrivateIpAddress;
      instance.updatedAt = new Date().toISOString();
    }
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        instance
      })
    };
  } catch (error) {
    console.error('Error getting instance:', error);
    
    return {
      statusCode: 500,
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

// インスタンス更新
exports.updateInstance = async (event) => {
  try {
    // ユーザーIDを取得（認証情報から）
    const userId = event.requestContext.authorizer.claims.sub;
    
    if (!userId) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Unauthorized'
        })
      };
    }
    
    const instanceId = event.pathParameters.id;
    const { name } = JSON.parse(event.body);
    
    // インスタンス情報を取得
    const instance = mockInstances[instanceId];
    
    if (!instance) {
      return {
        statusCode: 404,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Instance not found'
        })
      };
    }
    
    // 権限チェック
    if (instance.userId !== userId) {
      return {
        statusCode: 403,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Forbidden'
        })
      };
    }
    
    // インスタンス情報を更新
    instance.name = name;
    instance.updatedAt = new Date().toISOString();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        instance
      })
    };
  } catch (error) {
    console.error('Error updating instance:', error);
    
    return {
      statusCode: 500,
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

// インスタンス起動
exports.startInstance = async (event) => {
  try {
    // ユーザーIDを取得（認証情報から）
    const userId = event.requestContext.authorizer.claims.sub;
    
    if (!userId) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Unauthorized'
        })
      };
    }
    
    const instanceId = event.pathParameters.id;
    
    // インスタンス情報を取得
    const instance = mockInstances[instanceId];
    
    if (!instance) {
      return {
        statusCode: 404,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Instance not found'
        })
      };
    }
    
    // 権限チェック
    if (instance.userId !== userId) {
      return {
        statusCode: 403,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Forbidden'
        })
      };
    }
    
    // EC2インスタンスを起動
    const ec2Instance = mockEC2Instances[instance.ec2InstanceId];
    
    if (ec2Instance) {
      ec2Instance.State.Name = 'pending';
    }
    
    // インスタンス情報を更新
    instance.status = 'pending';
    instance.updatedAt = new Date().toISOString();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        message: 'Instance started successfully'
      })
    };
  } catch (error) {
    console.error('Error starting instance:', error);
    
    return {
      statusCode: 500,
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

// インスタンス停止
exports.stopInstance = async (event) => {
  try {
    // ユーザーIDを取得（認証情報から）
    const userId = event.requestContext.authorizer.claims.sub;
    
    if (!userId) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Unauthorized'
        })
      };
    }
    
    const instanceId = event.pathParameters.id;
    
    // インスタンス情報を取得
    const instance = mockInstances[instanceId];
    
    if (!instance) {
      return {
        statusCode: 404,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Instance not found'
        })
      };
    }
    
    // 権限チェック
    if (instance.userId !== userId) {
      return {
        statusCode: 403,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Forbidden'
        })
      };
    }
    
    // EC2インスタンスを停止
    const ec2Instance = mockEC2Instances[instance.ec2InstanceId];
    
    if (ec2Instance) {
      ec2Instance.State.Name = 'stopping';
    }
    
    // インスタンス情報を更新
    instance.status = 'stopping';
    instance.updatedAt = new Date().toISOString();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        message: 'Instance stopped successfully'
      })
    };
  } catch (error) {
    console.error('Error stopping instance:', error);
    
    return {
      statusCode: 500,
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

// インスタンス削除
exports.deleteInstance = async (event) => {
  try {
    // ユーザーIDを取得（認証情報から）
    const userId = event.requestContext.authorizer.claims.sub;
    
    if (!userId) {
      return {
        statusCode: 401,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Unauthorized'
        })
      };
    }
    
    const instanceId = event.pathParameters.id;
    
    // インスタンス情報を取得
    const instance = mockInstances[instanceId];
    
    if (!instance) {
      return {
        statusCode: 404,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Instance not found'
        })
      };
    }
    
    // 権限チェック
    if (instance.userId !== userId) {
      return {
        statusCode: 403,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Credentials': true
        },
        body: JSON.stringify({
          success: false,
          message: 'Forbidden'
        })
      };
    }
    
    // EC2インスタンスを削除
    delete mockEC2Instances[instance.ec2InstanceId];
    
    // インスタンス情報を削除
    delete mockInstances[instanceId];
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        message: 'Instance deleted successfully'
      })
    };
  } catch (error) {
    console.error('Error deleting instance:', error);
    
    return {
      statusCode: 500,
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
  
  if (path === '/instances' && method === 'GET') {
    return await exports.listInstances(event);
  }
  
  if (path === '/instances' && method === 'POST') {
    return await exports.createInstance(event);
  }
  
  if (path.match(/\/instances\/[^\/]+$/) && method === 'GET') {
    return await exports.getInstance(event);
  }
  
  if (path.match(/\/instances\/[^\/]+$/) && method === 'PUT') {
    return await exports.updateInstance(event);
  }
  
  if (path.match(/\/instances\/[^\/]+$/) && method === 'DELETE') {
    return await exports.deleteInstance(event);
  }
  
  if (path.match(/\/instances\/[^\/]+\/start$/) && method === 'POST') {
    return await exports.startInstance(event);
  }
  
  if (path.match(/\/instances\/[^\/]+\/stop$/) && method === 'POST') {
    return await exports.stopInstance(event);
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