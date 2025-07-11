import { apiRequest } from './request';

// 获取HDFS配额列表
export const getHdfsQuotas = (params) => {
  return apiRequest({
    url: '/hdfs-quotas',
    method: 'get',
    params
  });
};

// 获取单个HDFS配额详情
export const getHdfsQuota = (id) => {
  return apiRequest({
    url: `/hdfs-quotas/${id}`,
    method: 'get'
  });
};

// 创建HDFS配额
export const createHdfsQuota = (data) => {
  return apiRequest({
    url: '/hdfs-quotas',
    method: 'post',
    data
  });
};

// 更新HDFS配额
export const updateHdfsQuota = (id, data) => {
  return apiRequest({
    url: `/hdfs-quotas/${id}`,
    method: 'put',
    data
  });
};

// 删除HDFS配额
export const deleteHdfsQuota = (id) => {
  return apiRequest({
    url: `/hdfs-quotas/${id}`,
    method: 'delete'
  });
};
