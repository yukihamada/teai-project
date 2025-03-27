// AWS認証・API連携クライアント

// 設定
const API_URL = 'https://[API_ID].execute-api.ap-northeast-1.amazonaws.com/prod';
const USER_POOL_ID = 'ap-northeast-1_wwnIacApg';
const CLIENT_ID = '7m687l847drhsqoo7ai0l10cps';

// ローカルストレージキー
const TOKEN_KEY = 'teai_token';
const REFRESH_TOKEN_KEY = 'teai_refresh_token';
const USER_KEY = 'teai_user';

// 認証関連の関数
async function signUp(email, password, name) {
  try {
    const response = await fetch(`${API_URL}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        password,
        name
      })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'サインアップに失敗しました');
    }
    
    return data;
  } catch (error) {
    console.error('Sign up error:', error);
    throw error;
  }
}

async function signIn(email, password) {
  try {
    const response = await fetch(`${API_URL}/auth/signin`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email,
        password
      })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'サインインに失敗しました');
    }
    
    // トークンを保存
    localStorage.setItem(TOKEN_KEY, data.token);
    localStorage.setItem(REFRESH_TOKEN_KEY, data.refreshToken);
    
    // ユーザー情報を取得
    await getUser();
    
    return data;
  } catch (error) {
    console.error('Sign in error:', error);
    throw error;
  }
}

async function signOut() {
  // ローカルストレージからトークンを削除
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function getUser() {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (!token) {
      throw new Error('認証されていません');
    }
    
    const response = await fetch(`${API_URL}/auth/user`, {
      method: 'GET',
      headers: {
        'Authorization': token
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'ユーザー情報の取得に失敗しました');
    }
    
    // ユーザー情報を保存
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    
    return data.user;
  } catch (error) {
    console.error('Get user error:', error);
    throw error;
  }
}

// インスタンス関連の関数
async function listInstances() {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (!token) {
      throw new Error('認証されていません');
    }
    
    const response = await fetch(`${API_URL}/instances`, {
      method: 'GET',
      headers: {
        'Authorization': token
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'インスタンス一覧の取得に失敗しました');
    }
    
    return data.instances;
  } catch (error) {
    console.error('List instances error:', error);
    throw error;
  }
}

async function createInstance(name, instanceType) {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (!token) {
      throw new Error('認証されていません');
    }
    
    const response = await fetch(`${API_URL}/instances`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token
      },
      body: JSON.stringify({
        name,
        instanceType
      })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'インスタンスの作成に失敗しました');
    }
    
    return data.instance;
  } catch (error) {
    console.error('Create instance error:', error);
    throw error;
  }
}

async function getInstance(id) {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (!token) {
      throw new Error('認証されていません');
    }
    
    const response = await fetch(`${API_URL}/instances/${id}`, {
      method: 'GET',
      headers: {
        'Authorization': token
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'インスタンスの取得に失敗しました');
    }
    
    return data.instance;
  } catch (error) {
    console.error('Get instance error:', error);
    throw error;
  }
}

async function deleteInstance(id) {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (!token) {
      throw new Error('認証されていません');
    }
    
    const response = await fetch(`${API_URL}/instances/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': token
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'インスタンスの削除に失敗しました');
    }
    
    return data;
  } catch (error) {
    console.error('Delete instance error:', error);
    throw error;
  }
}

// インスタンス起動
async function startInstance(id) {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (!token) {
      throw new Error('認証されていません');
    }
    
    const response = await fetch(`${API_URL}/instances/${id}/start`, {
      method: 'POST',
      headers: {
        'Authorization': token
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'インスタンスの起動に失敗しました');
    }
    
    return data;
  } catch (error) {
    console.error('Start instance error:', error);
    throw error;
  }
}

// インスタンス停止
async function stopInstance(id) {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (!token) {
      throw new Error('認証されていません');
    }
    
    const response = await fetch(`${API_URL}/instances/${id}/stop`, {
      method: 'POST',
      headers: {
        'Authorization': token
      }
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'インスタンスの停止に失敗しました');
    }
    
    return data;
  } catch (error) {
    console.error('Stop instance error:', error);
    throw error;
  }
}

// インスタンス更新
async function updateInstance(id, name) {
  try {
    const token = localStorage.getItem(TOKEN_KEY);
    
    if (!token) {
      throw new Error('認証されていません');
    }
    
    const response = await fetch(`${API_URL}/instances/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token
      },
      body: JSON.stringify({
        name
      })
    });
    
    const data = await response.json();
    
    if (!data.success) {
      throw new Error(data.message || 'インスタンスの更新に失敗しました');
    }
    
    return data.instance;
  } catch (error) {
    console.error('Update instance error:', error);
    throw error;
  }
}

// ヘルパー関数
function isAuthenticated() {
  return !!localStorage.getItem(TOKEN_KEY);
}

function getCurrentUser() {
  const userJson = localStorage.getItem(USER_KEY);
  return userJson ? JSON.parse(userJson) : null;
}