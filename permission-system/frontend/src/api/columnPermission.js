import request from '../utils/request';

// 获取字段权限列表
export function getColumnPermissions(params) {
  return request({
    url: '/column-permissions/',
    method: 'get',
    params,
  });
}

// 获取单个字段权限详情
export function getColumnPermission(id) {
  return request({
    url: `/column-permissions/${id}`,
    method: 'get',
  });
}

// 创建字段权限
export function createColumnPermission(data) {
  return request({
    url: '/column-permissions/',
    method: 'post',
    data,
  });
}

// 更新字段权限
export function updateColumnPermission(id, data) {
  return request({
    url: `/column-permissions/${id}`,
    method: 'put',
    data,
  });
}

// 删除字段权限
export function deleteColumnPermission(id) {
  return request({
    url: `/column-permissions/${id}`,
    method: 'delete',
  });
}
