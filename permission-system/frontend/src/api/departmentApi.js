import request from '../utils/request';

/**
 * 部门管理相关API服务
 */
const departmentApi = {
  /**
   * 获取所有部门
   * @param {Object} params - 查询参数，如分页信息
   * @returns {Promise} - API响应
   */
  getDepartments: (params = {}) => {
    return request.get(`/departments`, { params });
  },

  /**
   * 获取单个部门详情
   * @param {Number} departmentId - 部门ID
   * @returns {Promise} - API响应
   */
  getDepartment: (departmentId) => {
    return request.get(`/departments/${departmentId}`);
  },

  /**
   * 创建部门
   * @param {Object} departmentData - 部门数据
   * @returns {Promise} - API响应
   */
  createDepartment: (departmentData) => {
    return request.post(`/departments`, departmentData);
  },

  /**
   * 更新部门
   * @param {Number} departmentId - 部门ID
   * @param {Object} departmentData - 部门数据
   * @returns {Promise} - API响应
   */
  updateDepartment: (departmentId, departmentData) => {
    return request.put(`/departments/${departmentId}`, departmentData);
  },

  /**
   * 删除部门
   * @param {Number} departmentId - 部门ID
   * @returns {Promise} - API响应
   */
  deleteDepartment: (departmentId) => {
    return request.delete(`/departments/${departmentId}`);
  }
};

export default departmentApi;
