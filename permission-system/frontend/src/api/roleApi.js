import request from '../utils/request';

/**
 * 角色管理相关API服务
 */
const roleApi = {
  /**
   * 获取所有角色
   * @param {Object} params - 查询参数，如分页信息
   * @returns {Promise} - API响应
   */
  getRoles: (params = {}) => {
    return request.get(`/roles`, { params });
  },

  /**
   * 获取单个角色详情
   * @param {Number} roleId - 角色ID
   * @returns {Promise} - API响应
   */
  getRole: (roleId) => {
    return request.get(`/roles/${roleId}`);
  },

  /**
   * 创建角色
   * @param {Object} roleData - 角色数据
   * @returns {Promise} - API响应
   */
  createRole: (roleData) => {
    return request.post(`/roles`, roleData);
  },

  /**
   * 更新角色
   * @param {Number} roleId - 角色ID
   * @param {Object} roleData - 角色数据
   * @returns {Promise} - API响应
   */
  updateRole: (roleId, roleData) => {
    return request.put(`/roles/${roleId}`, roleData);
  },

  /**
   * 删除角色
   * @param {Number} roleId - 角色ID
   * @returns {Promise} - API响应
   */
  deleteRole: (roleId) => {
    return request.delete(`/roles/${roleId}`);
  }
};

export default roleApi;
