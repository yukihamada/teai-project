const AWS = require('aws-sdk');
const config = require('../config/env');
const { v4: uuidv4 } = require('uuid');

// リージョン設定
AWS.config.update({ region: config.region });
const dynamodb = new AWS.DynamoDB.DocumentClient();
const ec2 = new AWS.EC2();

// テーブル名
const INSTANCES_TABLE = process.env.INSTANCES_TABLE || config.tables.instances;

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
    
    // DynamoDBからインスタンス一覧を取得
    const params = {
      TableName: INSTANCES_TABLE,
      IndexName: 'UserIdIndex',
      KeyConditionExpression: 'userId = :userId',
      ExpressionAttributeValues: {
        ':userId': userId
      }
    };
    
    const result = await dynamodb.query(params).promise();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        instances: result.Items
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
    
    // EC2インスタンスを作成
    const ec2Params = {
      ImageId: process.env.EC2_IMAGE_ID || config.ec2.defaultImageId,
      InstanceType: instanceType || process.env.EC2_INSTANCE_TYPE || config.ec2.defaultInstanceType,
      MinCount: 1,
      MaxCount: 1,
      TagSpecifications: [
        {
          ResourceType: 'instance',
          Tags: [
            {
              Key: 'Name',
              Value: name
            },
            {
              Key: 'UserId',
              Value: userId
            },
            {
              Key: 'Environment',
              Value: process.env.NODE_ENV || 'development'
            }
          ]
        }
      ]
    };
    
    const ec2Result = await ec2.runInstances(ec2Params).promise();
    const ec2InstanceId = ec2Result.Instances[0].InstanceId;
    
    // インスタンスの詳細情報を取得
    const describeParams = {
      InstanceIds: [ec2InstanceId]
    };
    
    // インスタンスが起動するまで待機
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const describeResult = await ec2.describeInstances(describeParams).promise();
    const instance = describeResult.Reservations[0].Instances[0];
    const ipAddress = instance.PublicIpAddress || instance.PrivateIpAddress;
    
    // DynamoDBにインスタンス情報を保存
    const instanceId = uuidv4();
    const dbParams = {
      TableName: INSTANCES_TABLE,
      Item: {
        id: instanceId,
        userId: userId,
        name: name,
        instanceType: instanceType || 't3a.large',
        ec2InstanceId: ec2InstanceId,
        ipAddress: ipAddress,
        status: 'running',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      }
    };
    
    await dynamodb.put(dbParams).promise();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        instance: dbParams.Item
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
    
    // DynamoDBからインスタンス情報を取得
    const params = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      }
    };
    
    const result = await dynamodb.get(params).promise();
    
    if (!result.Item) {
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
    if (result.Item.userId !== userId) {
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
    const ec2Params = {
      InstanceIds: [result.Item.ec2InstanceId]
    };
    
    const ec2Result = await ec2.describeInstances(ec2Params).promise();
    
    if (ec2Result.Reservations.length > 0 && ec2Result.Reservations[0].Instances.length > 0) {
      const ec2Instance = ec2Result.Reservations[0].Instances[0];
      
      // インスタンス情報を更新
      result.Item.status = ec2Instance.State.Name;
      result.Item.ipAddress = ec2Instance.PublicIpAddress || ec2Instance.PrivateIpAddress;
      
      // DynamoDBを更新
      const updateParams = {
        TableName: INSTANCES_TABLE,
        Key: {
          id: instanceId
        },
        UpdateExpression: 'set #status = :status, ipAddress = :ipAddress, updatedAt = :updatedAt',
        ExpressionAttributeNames: {
          '#status': 'status'
        },
        ExpressionAttributeValues: {
          ':status': result.Item.status,
          ':ipAddress': result.Item.ipAddress,
          ':updatedAt': new Date().toISOString()
        }
      };
      
      await dynamodb.update(updateParams).promise();
    }
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        instance: result.Item
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
    
    // DynamoDBからインスタンス情報を取得
    const params = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      }
    };
    
    const result = await dynamodb.get(params).promise();
    
    if (!result.Item) {
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
    if (result.Item.userId !== userId) {
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
    
    // EC2インスタンスを終了
    const ec2Params = {
      InstanceIds: [result.Item.ec2InstanceId]
    };
    
    await ec2.terminateInstances(ec2Params).promise();
    
    // DynamoDBからインスタンス情報を削除
    const deleteParams = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      }
    };
    
    await dynamodb.delete(deleteParams).promise();
    
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
    
    // DynamoDBからインスタンス情報を取得
    const params = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      }
    };
    
    const result = await dynamodb.get(params).promise();
    
    if (!result.Item) {
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
    if (result.Item.userId !== userId) {
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
    const ec2Params = {
      InstanceIds: [result.Item.ec2InstanceId]
    };
    
    await ec2.startInstances(ec2Params).promise();
    
    // DynamoDBを更新
    const updateParams = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      },
      UpdateExpression: 'set #status = :status, updatedAt = :updatedAt',
      ExpressionAttributeNames: {
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':status': 'pending',
        ':updatedAt': new Date().toISOString()
      }
    };
    
    await dynamodb.update(updateParams).promise();
    
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
    
    // DynamoDBからインスタンス情報を取得
    const params = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      }
    };
    
    const result = await dynamodb.get(params).promise();
    
    if (!result.Item) {
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
    if (result.Item.userId !== userId) {
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
    const ec2Params = {
      InstanceIds: [result.Item.ec2InstanceId]
    };
    
    await ec2.stopInstances(ec2Params).promise();
    
    // DynamoDBを更新
    const updateParams = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      },
      UpdateExpression: 'set #status = :status, updatedAt = :updatedAt',
      ExpressionAttributeNames: {
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':status': 'stopping',
        ':updatedAt': new Date().toISOString()
      }
    };
    
    await dynamodb.update(updateParams).promise();
    
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
    
    // DynamoDBからインスタンス情報を取得
    const params = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      }
    };
    
    const result = await dynamodb.get(params).promise();
    
    if (!result.Item) {
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
    if (result.Item.userId !== userId) {
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
    
    // EC2インスタンスのタグを更新
    if (name) {
      const ec2Params = {
        Resources: [result.Item.ec2InstanceId],
        Tags: [
          {
            Key: 'Name',
            Value: name
          }
        ]
      };
      
      await ec2.createTags(ec2Params).promise();
    }
    
    // DynamoDBを更新
    const updateParams = {
      TableName: INSTANCES_TABLE,
      Key: {
        id: instanceId
      },
      UpdateExpression: 'set #name = :name, updatedAt = :updatedAt',
      ExpressionAttributeNames: {
        '#name': 'name'
      },
      ExpressionAttributeValues: {
        ':name': name,
        ':updatedAt': new Date().toISOString()
      }
    };
    
    await dynamodb.update(updateParams).promise();
    
    // 更新後のインスタンス情報を取得
    const updatedResult = await dynamodb.get(params).promise();
    
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': true
      },
      body: JSON.stringify({
        success: true,
        instance: updatedResult.Item
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
  
  if (path === '/instances' && method === 'GET') {
    return await exports.listInstances(event);
  }
  
  if (path === '/instances' && method === 'POST') {
    return await exports.createInstance(event);
  }
  
  if (path.match(/\/instances\/[^\/]+$/) && method === 'GET') {
    return await exports.getInstance(event);
  }
  
  if (path.match(/\/instances\/[^\/]+$/) && method === 'DELETE') {
    return await exports.deleteInstance(event);
  }
  
  if (path.match(/\/instances\/[^\/]+$/) && method === 'PUT') {
    return await exports.updateInstance(event);
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