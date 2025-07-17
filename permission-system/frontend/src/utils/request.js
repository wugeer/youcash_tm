import axios from 'axios';
import { message, Modal } from 'antd';
import React from 'react';

// 创建axios实例
const service = axios.create({
  baseURL: window.APP_CONFIG?.API_URL || '/api/v1',
  timeout: 10000,
});

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    // 对响应数据做点什么
    return response.data;
  },
  (error) => {
    console.error('API Error:', error.response || error);
    // 添加更详细的错误日志，打印完整的错误结构
    console.log('错误对象类型:', typeof error);
    console.log('错误状态码:', error.response?.status);
    console.log('响应头信息:', error.response?.headers);
    
    if (error.response && error.response.data) {
      console.log('完整错误数据结构:', JSON.stringify(error.response.data, null, 2));
      // 添加Docker环境检测
      if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
        console.log('检测到Docker/远程环境，错误响应可能需要特殊处理');
      }
    }

    if (error.response && error.response.data) {
      const errorData = error.response.data;
      let titleMessage = errorData.message || '操作失败';
      let errorContent = null;
      
      // Docker环境特殊处理
      const isDockerOrRemoteEnv = window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1';
      console.log(`当前环境: ${isDockerOrRemoteEnv ? 'Docker/远程' : '本地'}, hostname: ${window.location.hostname}`);
      
      // 综合处理出错情况，按优先级检查各种可能的错误结构
      
      // 0. 通用错误提取函数
      const extractErrorText = (e) => {
        if (typeof e === 'string') return e;
        if (e && typeof e === 'object') {
          return e.error || e.msg || e.detail || e.message || JSON.stringify(e);
        }
        return JSON.stringify(e);
      };
      
      // 1. 先检查是否存在 response.data.errors 或 failed_records 数组
      if ((Array.isArray(errorData.errors) && errorData.errors.length > 0) ||
          (Array.isArray(errorData.failed_records) && errorData.failed_records.length > 0)) {
        const errors = errorData.errors || errorData.failed_records;
        const errorElements = errors.map((e, index) => {
          let errorText = extractErrorText(e);
          return React.createElement('div', { key: index }, `${index + 1}. ${errorText}`);
        });
        
        errorContent = React.createElement('div', { style: { maxHeight: '400px', overflowY: 'auto' } }, errorElements);
      }
      // 2. 检查 response.data.detail 是否为对象并包含 errors 数组
      else if (errorData.detail && typeof errorData.detail === 'object' && errorData.detail !== null) {
        // 检查是否有 detail.errors 数组
        if (Array.isArray(errorData.detail.errors) && errorData.detail.errors.length > 0) {
          titleMessage = errorData.detail.message || titleMessage;
          const errorElements = errorData.detail.errors.map((e, index) => {
            let errorText = extractErrorText(e);
            return React.createElement('div', { key: index }, `${index + 1}. ${errorText}`);
          });
          errorContent = React.createElement('div', { style: { maxHeight: '400px', overflowY: 'auto' } }, errorElements);
        } else {
          // 如果没有 errors 数组，显示 detail.message 或整个 detail 对象
          const contentMessage = errorData.detail.message || JSON.stringify(errorData.detail);
          errorContent = React.createElement('div', {}, contentMessage);
        }
      }
      // 3. 如果 response.data.detail 是字符串
      else if (typeof errorData.detail === 'string') {
        errorContent = React.createElement('div', {}, errorData.detail);
      }
      // 4. Docker环境下，尝试额外的错误格式
      else if (isDockerOrRemoteEnv && errorData) {
        // 尝试从响应中提取错误信息
        if (typeof errorData === 'string') {
          errorContent = React.createElement('div', {}, errorData);
        } else {
          // 尝试分析JSON并查找可能的错误字段
          const possibleErrorFields = ['error', 'message', 'msg', 'detail'];
          for (const field of possibleErrorFields) {
            if (errorData[field]) {
              const fieldValue = errorData[field];
              if (typeof fieldValue === 'string') {
                errorContent = React.createElement('div', {}, fieldValue);
                break;
              } else if (typeof fieldValue === 'object') {
                errorContent = React.createElement('pre', { 
                  style: { whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto' } 
                }, JSON.stringify(fieldValue, null, 2));
                break;
              }
            }
          }
        }
      }
      
      // 5. 如果所有分支都没有匹配，显示整个错误对象
      if (!errorContent) {
        const responseStr = typeof errorData === 'string' ? errorData : JSON.stringify(errorData, null, 2);
        errorContent = React.createElement('pre', { 
          style: { whiteSpace: 'pre-wrap', maxHeight: '400px', overflowY: 'auto' } 
        }, responseStr);
      }
      
      // 显示错误对话框
      Modal.error({
        title: titleMessage,
        content: errorContent,
        width: 600,
      });
      
      return Promise.reject(error);

    } else {
      // 处理网络错误或其他未知错误
      message.error(error.message || '网络错误，请检查您的连接');
    }

    return Promise.reject(error);
  }
);

export default service;
