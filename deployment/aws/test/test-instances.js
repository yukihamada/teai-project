// インスタンス管理APIのテスト

// モックイベント
const listInstancesEvent = {
  path: '/instances',
  httpMethod: 'GET',
  requestContext: {
    authorizer: {
      claims: {
        sub: 'test-user-id'
      }
    }
  }
};

const createInstanceEvent = {
  path: '/instances',
  httpMethod: 'POST',
  requestContext: {
    authorizer: {
      claims: {
        sub: 'test-user-id'
      }
    }
  },
  body: JSON.stringify({
    name: 'Test Instance',
    instanceType: 't3a.large'
  })
};

const getInstanceEvent = {
  path: '/instances/34ad8b76-f050-4f05-8515-de3b9685c19c',
  httpMethod: 'GET',
  requestContext: {
    authorizer: {
      claims: {
        sub: 'test-user-id'
      }
    }
  },
  pathParameters: {
    id: '34ad8b76-f050-4f05-8515-de3b9685c19c'
  }
};

const updateInstanceEvent = {
  path: '/instances/34ad8b76-f050-4f05-8515-de3b9685c19c',
  httpMethod: 'PUT',
  requestContext: {
    authorizer: {
      claims: {
        sub: 'test-user-id'
      }
    }
  },
  pathParameters: {
    id: '34ad8b76-f050-4f05-8515-de3b9685c19c'
  },
  body: JSON.stringify({
    name: 'Updated Test Instance'
  })
};

const startInstanceEvent = {
  path: '/instances/34ad8b76-f050-4f05-8515-de3b9685c19c/start',
  httpMethod: 'POST',
  requestContext: {
    authorizer: {
      claims: {
        sub: 'test-user-id'
      }
    }
  },
  pathParameters: {
    id: '34ad8b76-f050-4f05-8515-de3b9685c19c'
  }
};

const stopInstanceEvent = {
  path: '/instances/34ad8b76-f050-4f05-8515-de3b9685c19c/stop',
  httpMethod: 'POST',
  requestContext: {
    authorizer: {
      claims: {
        sub: 'test-user-id'
      }
    }
  },
  pathParameters: {
    id: '34ad8b76-f050-4f05-8515-de3b9685c19c'
  }
};

const deleteInstanceEvent = {
  path: '/instances/34ad8b76-f050-4f05-8515-de3b9685c19c',
  httpMethod: 'DELETE',
  requestContext: {
    authorizer: {
      claims: {
        sub: 'test-user-id'
      }
    }
  },
  pathParameters: {
    id: '34ad8b76-f050-4f05-8515-de3b9685c19c'
  }
};

// モック関数をインポート
const instancesHandler = require('./mock-instances').handler;

// テスト実行
async function runTests() {
  console.log('=== インスタンス管理APIテスト開始 ===');
  
  try {
    // インスタンス一覧取得テスト
    console.log('\n--- インスタンス一覧取得テスト ---');
    const listInstancesResult = await instancesHandler(listInstancesEvent);
    console.log('ステータスコード:', listInstancesResult.statusCode);
    console.log('レスポンス:', listInstancesResult.body);
    
    // インスタンス作成テスト
    console.log('\n--- インスタンス作成テスト ---');
    const createInstanceResult = await instancesHandler(createInstanceEvent);
    console.log('ステータスコード:', createInstanceResult.statusCode);
    console.log('レスポンス:', createInstanceResult.body);
    
    // インスタンス取得テスト
    console.log('\n--- インスタンス取得テスト ---');
    const getInstanceResult = await instancesHandler(getInstanceEvent);
    console.log('ステータスコード:', getInstanceResult.statusCode);
    console.log('レスポンス:', getInstanceResult.body);
    
    // インスタンス更新テスト
    console.log('\n--- インスタンス更新テスト ---');
    const updateInstanceResult = await instancesHandler(updateInstanceEvent);
    console.log('ステータスコード:', updateInstanceResult.statusCode);
    console.log('レスポンス:', updateInstanceResult.body);
    
    // インスタンス起動テスト
    console.log('\n--- インスタンス起動テスト ---');
    const startInstanceResult = await instancesHandler(startInstanceEvent);
    console.log('ステータスコード:', startInstanceResult.statusCode);
    console.log('レスポンス:', startInstanceResult.body);
    
    // インスタンス停止テスト
    console.log('\n--- インスタンス停止テスト ---');
    const stopInstanceResult = await instancesHandler(stopInstanceEvent);
    console.log('ステータスコード:', stopInstanceResult.statusCode);
    console.log('レスポンス:', stopInstanceResult.body);
    
    // インスタンス削除テスト
    console.log('\n--- インスタンス削除テスト ---');
    const deleteInstanceResult = await instancesHandler(deleteInstanceEvent);
    console.log('ステータスコード:', deleteInstanceResult.statusCode);
    console.log('レスポンス:', deleteInstanceResult.body);
    
    console.log('\n=== インスタンス管理APIテスト完了 ===');
  } catch (error) {
    console.error('テスト実行中にエラーが発生しました:', error);
  }
}

// テスト実行
runTests();