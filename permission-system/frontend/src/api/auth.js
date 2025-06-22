import request from '../utils/request';

// 用户登录
export function login(data) {
  console.log('auth.js login - 原始数据:', JSON.stringify(data));
  console.log('auth.js login - 密码长度:', data.password ? data.password.length : 0);
  
  // 创建新对象传递，避免引用修改
  const loginData = {
    username: data.username,
    password: data.password
  };
  
  console.log('auth.js login - 即将发送的数据:', JSON.stringify(loginData));
  return request({
    url: '/auth/login/json',
    method: 'post',
    data: loginData,
  });
}

// 用户注册
export function register(data) {
  return request({
    url: '/auth/register',
    method: 'post',
    data,
  });
}

// 获取当前用户信息
export function getUserInfo() {
  return request({
    url: '/auth/me',
    method: 'get',
  });
}

// 创建管理员用户(首次使用系统)
export function createAdminUser(data) {
  return request({
    url: '/auth/create-admin',
    method: 'post',
    data,
  });
}
