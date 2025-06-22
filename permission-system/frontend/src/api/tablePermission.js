import request from '../utils/request';

// 获取表权限列表
export function getTablePermissions(params) {
  return request({
    url: '/table-permissions/',
    method: 'get',
    params,
  });
}

// 获取单个表权限详情
export function getTablePermission(id) {
  return request({
    url: `/table-permissions/${id}`,
    method: 'get',
  });
}

// 创建表权限
export function createTablePermission(data) {
  return request({
    url: '/table-permissions/',
    method: 'post',
    data,
  });
}

// 更新表权限
export function updateTablePermission(id, data) {
  return request({
    url: `/table-permissions/${id}`,
    method: 'put',
    data,
  });
}

// 删除表权限
export function deleteTablePermission(id) {
  return request({
    url: `/table-permissions/${id}`,
    method: 'delete',
  });
}
