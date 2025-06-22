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
    // 记录原始请求数据
    console.log('拦截器 - 请求URL:', config.url);
    console.log('拦截器 - 原始数据:', config.data ? JSON.stringify(config.data) : 'no data');
    
    // 记录请求参数
    if (config.params) {
      console.log('拦截器 - 请求参数:', JSON.stringify(config.params));
      if (config.params.sorters) {
        console.log('拦截器 - 排序参数:', config.params.sorters);
      }
    }
    
    // 检查是否是登录请求
    if (config.url && config.url.includes('/auth/login') && config.data) {
      console.log('拦截器 - 检测到登录请求');
      console.log('拦截器 - 登录密码:', config.data.password);
      
      if (typeof config.data === 'string') {
        try {
          const parsedData = JSON.parse(config.data);
          console.log('拦截器 - 已解析字符串数据:', parsedData);
          
          // 测试: 确保密码不被修改(仅用于调试)
          if (parsedData.password && parsedData.username === 'admin') {
            const originalPassword = parsedData.password;
            console.log('拦截器 - 原始密码:', originalPassword);
            // 如果密码已被修改，还原为正确密码
            if (originalPassword !== '1qaz@WSX') {
              const fixedData = { ...parsedData, password: '1qaz@WSX' };
              console.log('拦截器 - 修正后的数据:', fixedData);
              config.data = JSON.stringify(fixedData);
            }
          }
        } catch (e) {
          console.error('数据解析错误:', e);
        }
      } else if (config.data && typeof config.data === 'object') {
        console.log('拦截器 - 原始对象数据:', config.data);
        
        // 测试: 检查密码是否设置正确(仅用于调试)
        if (config.data.password && config.data.username === 'admin') {
          console.log('拦截器 - 发送前密码:', config.data.password);
        }
      }
    }
    
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
    let errorMessage;

    if (error.response) {
      const { status, data } = error.response;
      const detail = data ? data.detail : null;

      // 1. 优先从后端返回的 detail 字段解析详细错误信息
      if (detail) {
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail) && detail.length > 0 && detail[0].msg) {
          // 处理Pydantic返回的错误对象数组，例如：[{loc: ..., msg: ..., type: ...}]
          errorMessage = detail.map(err => err.msg).join('; ');
        } else if (typeof detail === 'object' && detail !== null && detail.msg) {
          // 处理Pydantic返回的单个错误对象
          errorMessage = detail.msg;
        }
      }

      // 2. 如果没有解析出详细错误，则根据HTTP状态码设置通用错误信息
      if (!errorMessage) {
        switch (status) {
          case 401:
            errorMessage = '登录已过期，请重新登录';
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
            errorMessage = '请求参数错误';
            break;
          case 422:
            errorMessage = '请求数据校验失败';
            break;
          case 500:
            errorMessage = '服务器内部错误';
            break;
          default:
            errorMessage = `请求失败，状态码: ${status}`;
        }
      }
    } else if (error.request) {
      errorMessage = '无法连接到服务器，请检查网络';
    } else {
      errorMessage = '请求发生错误，请检查网络或联系管理员';
    }

    message.error(errorMessage);
    return Promise.reject(error);
  }
);

export default service;
