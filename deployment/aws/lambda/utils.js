/**
 * 共通ユーティリティ関数
 */

const config = require('../config/env');

/**
 * 標準レスポンスヘッダーを生成する
 * @returns {Object} CORSヘッダーを含むレスポンスヘッダー
 */
exports.getResponseHeaders = () => {
  return {
    'Access-Control-Allow-Origin': config.cors.allowOrigin,
    'Access-Control-Allow-Credentials': true
  };
};

/**
 * 成功レスポンスを生成する
 * @param {Object} data レスポンスデータ
 * @param {number} statusCode HTTPステータスコード（デフォルト: 200）
 * @returns {Object} 成功レスポンス
 */
exports.successResponse = (data, statusCode = 200) => {
  return {
    statusCode,
    headers: exports.getResponseHeaders(),
    body: JSON.stringify({
      success: true,
      ...data
    })
  };
};

/**
 * エラーレスポンスを生成する
 * @param {string} message エラーメッセージ
 * @param {number} statusCode HTTPステータスコード（デフォルト: 500）
 * @returns {Object} エラーレスポンス
 */
exports.errorResponse = (message, statusCode = 500) => {
  return {
    statusCode,
    headers: exports.getResponseHeaders(),
    body: JSON.stringify({
      success: false,
      message
    })
  };
};

/**
 * ログを出力する
 * @param {string} level ログレベル（info, warn, error）
 * @param {string} message ログメッセージ
 * @param {Object} data 追加データ
 */
exports.log = (level, message, data = {}) => {
  const logEntry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    environment: process.env.NODE_ENV || 'development',
    ...data
  };
  
  // 本番環境ではエラーのみ出力
  if (process.env.NODE_ENV === 'production' && level !== 'error') {
    return;
  }
  
  console.log(JSON.stringify(logEntry));
};