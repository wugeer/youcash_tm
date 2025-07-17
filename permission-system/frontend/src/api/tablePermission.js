import request from '../utils/request';

// 获取表权限列表
export function getTablePermissions(params) {
  return request({
    url: '/table-permissions/',
    method: 'get',
    params,
  });
}

// 批量创建表权限
export function batchCreateTablePermissions(data) {
  // 确保数据是正确的格式: { items: [], batch_sync: false }
  let formattedData = data;
  
  // 如果收到的是数组，自动包装为正确的格式
  if (Array.isArray(data)) {
    console.log('批量导入API - 检测到数组格式，自动转换为正确格式');
    formattedData = {
      items: data,
      batch_sync: false
    };
  } else if (data && !data.items) {
    // 如果不是数组但也缺少items字段，则将其包装为正确格式
    console.log('批量导入API - 检测到缺少items字段，自动转换为正确格式');
    formattedData = {
      items: [data],
      batch_sync: false
    };
  }
  
  console.log('批量导入API - 发送数据格式:', JSON.stringify(formattedData));
  
  return request({
    url: '/table-permissions/batch',
    method: 'post',
    data: formattedData,
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

// 同步表权限
export function syncTablePermissions() {
  return request({
    url: '/table-permissions/sync',
    method: 'post',
  });
}

// 同步单个表权限
export function syncTablePermission(id) {
  return request({
    url: `/table-permissions/sync/${id}`,
    method: 'post',
  });
}

// 删除表权限
export function deleteTablePermission(id) {
  return request({
    url: `/table-permissions/${id}`,
    method: 'delete',
  });
}
