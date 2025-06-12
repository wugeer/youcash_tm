import request from '../utils/request';

// 用户登录
export function login(data) {
  return request({
    url: '/auth/login/json',
    method: 'post',
    data,
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
