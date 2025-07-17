import request from '../utils/request';

// 获取行权限列表
export function getRowPermissions(params) {
  return request({
    url: '/row-permissions/',
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
    url: '/row-permissions/',
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

// 同步行权限
export function syncRowPermissions() {
  return request({
    url: '/row-permissions/sync',
    method: 'post',
  });
}

// 删除行权限
export function deleteRowPermission(id) {
  return request({
    url: `/row-permissions/${id}`,
    method: 'delete',
  });
}

// 同步单个行权限
export function syncRowPermission(id) {
  return request({
    url: `/row-permissions/sync/${id}`,
    method: 'post',
  });
}

// 批量创建行权限
export function batchCreateRowPermissions(data) {
  // 确保数据是正确的格式: { items: [], batch_sync: false }
  let formattedData = data;
  
  // 如果收到的是数组，自动包装为正确的格式
  if (Array.isArray(data)) {
    console.log('行权限批量导入API - 检测到数组格式，自动转换为正确格式');
    formattedData = {
      items: data,
      batch_sync: false
    };
  } else if (data && !data.items) {
    // 如果不是数组但也缺少items字段，则将其包装为正确格式
    console.log('行权限批量导入API - 检测到缺少items字段，自动转换为正确格式');
    formattedData = {
      items: [data],
      batch_sync: false
    };
  }
  
  console.log('行权限批量导入API - 发送数据格式:', JSON.stringify(formattedData));
  
  return request({
    url: '/row-permissions/batch',
    method: 'post',
    data: formattedData,
  });
}
