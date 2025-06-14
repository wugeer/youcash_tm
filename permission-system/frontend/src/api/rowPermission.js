import request from '../utils/request';

// 获取行权限列表
export function getRowPermissions(params) {
  return request({
    url: '/row-permissions',
    method: 'get',
    params,
  });
}

// 获取单个行权限详情
export function getRowPermission(id) {
  return request({
    url: `/row-permissions/${id}`,
    method: 'get',
  });
}

// 创建行权限
export function createRowPermission(data) {
  return request({
    url: '/row-permissions',
    method: 'post',
    data,
  });
}

// 更新行权限
export function updateRowPermission(id, data) {
  return request({
    url: `/row-permissions/${id}`,
    method: 'put',
    data,
  });
}

// 删除行权限
export function deleteRowPermission(id) {
  return request({
    url: `/row-permissions/${id}`,
    method: 'delete',
  });
}
