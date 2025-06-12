import axios from 'axios';
import { message } from 'antd';

// 创建axios实例
const service = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
});

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    let errorMessage = '请求失败，请稍后重试';
    
    if (error.response) {
      const { status, data } = error.response;
      
      // 处理特定状态码
      switch (status) {
        case 401:
          errorMessage = '登录已过期，请重新登录';
          // 清除token并重定向到登录页
          localStorage.removeItem('token');
          window.location.href = '/login';
          break;
        case 403:
          errorMessage = '没有权限访问该资源';
          break;
        case 404:
          errorMessage = '请求的资源不存在';
          break;
        case 400:
          errorMessage = data.detail || '请求参数错误';
          break;
        case 500:
          errorMessage = '服务器内部错误';
          break;
        default:
          errorMessage = data.detail || '请求失败，请稍后重试';
      }
    } else if (error.request) {
      errorMessage = '无法连接到服务器，请检查网络';
    }
    
    message.error(errorMessage);
    return Promise.reject(error);
  }
);

export default service;
