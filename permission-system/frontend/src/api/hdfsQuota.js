import request from '../utils/request';

// 同步HDFS配额
export function syncHdfsQuotas() {
  return request({
    url: '/hdfs-quotas/sync',
    method: 'post',
  });
}

// 同步单个HDFS配额
export function syncHdfsQuota(id) {
  return request({
    url: `/hdfs-quotas/sync/${id}`,
    method: 'post',
  });
}


// 获取HDFS配额列表
export const getHdfsQuotas = (params) => {
  return request({
    url: '/hdfs-quotas',
    method: 'get',
    params
  });
};

// 获取单个HDFS配额详情
export const getHdfsQuota = (id) => {
  return request({
    url: `/hdfs-quotas/${id}`,
    method: 'get'
  });
};

// 创建HDFS配额
export const createHdfsQuota = (data) => {
  return request({
    url: '/hdfs-quotas',
    method: 'post',
    data
  });
};

// 更新HDFS配额
export const updateHdfsQuota = (id, data) => {
  return request({
    url: `/hdfs-quotas/${id}`,
    method: 'put',
    data
  });
};

// 删除HDFS配额
export const deleteHdfsQuota = (id) => {
  return request({
    url: `/hdfs-quotas/${id}`,
    method: 'delete'
  });
};

/**
 * 批量导入HDFS配额
 * @param {Array|Object} data - 要导入的HDFS配额数据数组或对象
 * @returns {Promise} - 返回导入结果
 */
export function batchImportHdfsQuotas(data) {
  // 确保数据是正确的格式: { items: [], batch_sync: false }
  let formattedData = data;
  
  // 如果收到的是数组，自动包装为正确的格式
  if (Array.isArray(data)) {
    console.log('HDFS配额批量导入API - 检测到数组格式，自动转换为正确格式');
    formattedData = {
      items: data,
      batch_sync: false
    };
  } else if (data && !data.items) {
    // 如果不是数组但也缺少items字段，则将其包装为正确格式
    console.log('HDFS配额批量导入API - 检测到缺少items字段，自动转换为正确格式');
    formattedData = {
      items: [data],
      batch_sync: false
    };
  }
  
  console.log('HDFS配额批量导入API - 发送数据格式:', JSON.stringify(formattedData));
  
  return request({
    url: '/hdfs-quotas/batch-import',
    method: 'post',
    data: formattedData,
  });
};
