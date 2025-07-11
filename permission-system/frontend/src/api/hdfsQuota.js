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
    url: `/hdfs-quotas/${id}/sync`,
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
 * @param {Array} data - 要导入的HDFS配额数据数组，每项包含db_name和hdfs_quota
 * @returns {Promise} - 返回导入结果
 */
export function batchImportHdfsQuotas(data) {
  return request({
    url: '/hdfs-quotas/batch-import',
    method: 'post',
    data,
  });
};
