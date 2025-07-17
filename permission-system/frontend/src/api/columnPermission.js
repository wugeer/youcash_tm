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

// 同步字段权限
export function syncColumnPermissions() {
  return request({
    url: '/column-permissions/sync',
    method: 'post',
  });
}

// 同步单个字段权限
export function syncColumnPermission(id) {
  return request({
    url: `/column-permissions/sync/${id}`,
    method: 'post',
  });
}

// 删除字段权限
export function deleteColumnPermission(id) {
  return request({
    url: `/column-permissions/${id}`,
    method: 'delete',
  });
}

// 批量创建字段权限
export function batchCreateColumnPermissions(data) {
  // 确保数据是正确的格式: { items: [], batch_sync: false }
  let formattedData = data;
  
  // 如果收到的是数组，自动包装为正确的格式
  if (Array.isArray(data)) {
    console.log('列权限批量导入API - 检测到数组格式，自动转换为正确格式');
    formattedData = {
      items: data,
      batch_sync: false
    };
  } else if (data && !data.items) {
    // 如果不是数组但也缺少items字段，则将其包装为正确格式
    console.log('列权限批量导入API - 检测到缺少items字段，自动转换为正确格式');
    formattedData = {
      items: [data],
      batch_sync: false
    };
  }
  
  console.log('列权限批量导入API - 发送数据格式:', JSON.stringify(formattedData));
  
  return request({
    url: '/column-permissions/batch',
    method: 'post',
    data: formattedData,
  });
}
