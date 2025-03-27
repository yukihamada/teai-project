// AWS SDKのモック
// リージョン設定
const config = {
  update: () => {}
};

// DynamoDBのモック
const mockDynamoDBItems = {
  'teai-profiles': {
    'test-user-id': {
      id: 'test-user-id',
      email: 'test@example.com',
      name: 'Test User',
      createdAt: '2025-03-27T00:00:00.000Z'
    }
  },
  'teai-instances': {
    'test-instance-id': {
      id: 'test-instance-id',
      userId: 'test-user-id',
      name: 'Test Instance',
      instanceType: 't3a.large',
      ec2InstanceId: 'i-12345678901234567',
      ipAddress: '192.168.1.1',
      status: 'running',
      createdAt: '2025-03-27T00:00:00.000Z',
      updatedAt: '2025-03-27T00:00:00.000Z'
    }
  }
};

// Cognitoのモック
const mockCognitoUsers = {
  'test@example.com': {
    Username: 'test@example.com',
    UserAttributes: [
      {
        Name: 'sub',
        Value: 'test-user-id'
      },
      {
        Name: 'email',
        Value: 'test@example.com'
      },
      {
        Name: 'name',
        Value: 'Test User'
      },
      {
        Name: 'email_verified',
        Value: 'true'
      }
    ],
    Confirmed: true
  }
};

// EC2のモック
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

// AWS SDKのモック
const AWS = {
  config: config,
  DynamoDB: {
    DocumentClient: function() {
      return {
        get: params => {
          return {
            promise: () => {
              const tableName = params.TableName;
              const key = params.Key.id;
              
              if (mockDynamoDBItems[tableName] && mockDynamoDBItems[tableName][key]) {
                return Promise.resolve({
                  Item: mockDynamoDBItems[tableName][key]
                });
              }
              
              return Promise.resolve({
                Item: null
              });
            }
          };
        },
        put: params => {
          return {
            promise: () => {
              const tableName = params.TableName;
              const item = params.Item;
              
              if (!mockDynamoDBItems[tableName]) {
                mockDynamoDBItems[tableName] = {};
              }
              
              mockDynamoDBItems[tableName][item.id] = item;
              
              return Promise.resolve({});
            }
          };
        },
        update: params => {
          return {
            promise: () => {
              const tableName = params.TableName;
              const key = params.Key.id;
              
              if (mockDynamoDBItems[tableName] && mockDynamoDBItems[tableName][key]) {
                // 簡易的な更新処理
                mockDynamoDBItems[tableName][key].updatedAt = new Date().toISOString();
                
                if (params.ExpressionAttributeValues[':name']) {
                  mockDynamoDBItems[tableName][key].name = params.ExpressionAttributeValues[':name'];
                }
                
                if (params.ExpressionAttributeValues[':status']) {
                  mockDynamoDBItems[tableName][key].status = params.ExpressionAttributeValues[':status'];
                }
                
                if (params.ExpressionAttributeValues[':ipAddress']) {
                  mockDynamoDBItems[tableName][key].ipAddress = params.ExpressionAttributeValues[':ipAddress'];
                }
              }
              
              return Promise.resolve({});
            }
          };
        },
        delete: params => {
          return {
            promise: () => {
              const tableName = params.TableName;
              const key = params.Key.id;
              
              if (mockDynamoDBItems[tableName] && mockDynamoDBItems[tableName][key]) {
                delete mockDynamoDBItems[tableName][key];
              }
              
              return Promise.resolve({});
            }
          };
        },
        query: params => {
          return {
            promise: () => {
              const tableName = params.TableName;
              const userId = params.ExpressionAttributeValues[':userId'];
              
              if (mockDynamoDBItems[tableName]) {
                const items = Object.values(mockDynamoDBItems[tableName])
                  .filter(item => item.userId === userId);
                
                return Promise.resolve({
                  Items: items
                });
              }
              
              return Promise.resolve({
                Items: []
              });
            }
          };
        }
      };
    }
  },
  CognitoIdentityServiceProvider: function() {
    return {
      signUp: params => {
        return {
          promise: () => {
            const email = params.Username;
            
            // テスト用に常に成功を返す
            const userId = 'test-user-id';
            
            // ユーザーが存在しない場合は作成
            if (!mockCognitoUsers[email]) {
              mockCognitoUsers[email] = {
                Username: email,
                UserAttributes: [
                  {
                    Name: 'sub',
                    Value: userId
                  },
                  {
                    Name: 'email',
                    Value: email
                  },
                  {
                    Name: 'name',
                    Value: params.UserAttributes.find(attr => attr.Name === 'name')?.Value || ''
                  },
                  {
                    Name: 'email_verified',
                    Value: 'true'
                  }
                ],
                Confirmed: true
              };
            }
            
            return Promise.resolve({
              UserSub: userId
            });
          }
        };
      },
      initiateAuth: params => {
        return {
          promise: () => {
            const email = params.AuthParameters.USERNAME;
            const password = params.AuthParameters.PASSWORD;
            
            // ユーザーが存在するかチェック
            if (!mockCognitoUsers[email]) {
              return Promise.reject({
                code: 'UserNotFoundException',
                message: 'User does not exist'
              });
            }
            
            // ユーザーが確認済みかチェック
            if (!mockCognitoUsers[email].Confirmed) {
              return Promise.reject({
                code: 'UserNotConfirmedException',
                message: 'User is not confirmed'
              });
            }
            
            // パスワードチェック（モックなので実際には検証しない）
            
            return Promise.resolve({
              AuthenticationResult: {
                IdToken: 'dummy-id-token',
                RefreshToken: 'dummy-refresh-token',
                ExpiresIn: 3600
              }
            });
          }
        };
      },
      getUser: params => {
        return {
          promise: () => {
            // トークンの検証
            const token = params.AccessToken;
            if (token !== 'dummy-id-token') {
              return Promise.reject({
                code: 'NotAuthorizedException',
                message: 'Invalid Access Token'
              });
            }
            
            // トークンからユーザーを取得（モックなので固定値を返す）
            return Promise.resolve({
              Username: 'test@example.com',
              UserAttributes: [
                {
                  Name: 'sub',
                  Value: 'test-user-id'
                },
                {
                  Name: 'email',
                  Value: 'test@example.com'
                },
                {
                  Name: 'name',
                  Value: 'Test User'
                },
                {
                  Name: 'email_verified',
                  Value: 'true'
                }
              ]
            });
          }
        };
      }
    };
  },
  EC2: function() {
    return {
      runInstances: params => {
        return {
          promise: () => {
            // 新しいインスタンスを作成
            const instanceId = 'i-' + Math.random().toString(36).substring(2, 15);
            
            mockEC2Instances[instanceId] = {
              InstanceId: instanceId,
              State: {
                Name: 'pending'
              },
              PublicIpAddress: '192.168.1.' + Math.floor(Math.random() * 255),
              PrivateIpAddress: '10.0.0.' + Math.floor(Math.random() * 255)
            };
            
            return Promise.resolve({
              Instances: [
                {
                  InstanceId: instanceId
                }
              ]
            });
          }
        };
      },
      describeInstances: params => {
        return {
          promise: () => {
            const instanceIds = params.InstanceIds;
            const instances = instanceIds.map(id => mockEC2Instances[id]).filter(Boolean);
            
            return Promise.resolve({
              Reservations: [
                {
                  Instances: instances
                }
              ]
            });
          }
        };
      },
      startInstances: params => {
        return {
          promise: () => {
            const instanceIds = params.InstanceIds;
            
            instanceIds.forEach(id => {
              if (mockEC2Instances[id]) {
                mockEC2Instances[id].State.Name = 'pending';
              }
            });
            
            return Promise.resolve({
              StartingInstances: instanceIds.map(id => ({
                InstanceId: id,
                CurrentState: {
                  Name: 'pending'
                },
                PreviousState: {
                  Name: 'stopped'
                }
              }))
            });
          }
        };
      },
      stopInstances: params => {
        return {
          promise: () => {
            const instanceIds = params.InstanceIds;
            
            instanceIds.forEach(id => {
              if (mockEC2Instances[id]) {
                mockEC2Instances[id].State.Name = 'stopping';
              }
            });
            
            return Promise.resolve({
              StoppingInstances: instanceIds.map(id => ({
                InstanceId: id,
                CurrentState: {
                  Name: 'stopping'
                },
                PreviousState: {
                  Name: 'running'
                }
              }))
            });
          }
        };
      },
      terminateInstances: params => {
        return {
          promise: () => {
            const instanceIds = params.InstanceIds;
            
            instanceIds.forEach(id => {
              if (mockEC2Instances[id]) {
                mockEC2Instances[id].State.Name = 'shutting-down';
              }
            });
            
            return Promise.resolve({
              TerminatingInstances: instanceIds.map(id => ({
                InstanceId: id,
                CurrentState: {
                  Name: 'shutting-down'
                },
                PreviousState: {
                  Name: 'running'
                }
              }))
            });
          }
        };
      },
      createTags: params => {
        return {
          promise: () => {
            return Promise.resolve({});
          }
        };
      }
    };
  }
};

module.exports = AWS;