import axios from 'axios';
import request from '../utils/request';

// API基本路径 - 相对于request.js中的baseURL
const API_BASE_URL = '/ldap';

/**
 * LDAP用户管理相关API服务
 */
const ldapUserApi = {
  /**
   * 获取LDAP用户列表
   * @param {Object} params - 查询参数
   * @returns {Promise} - API响应
   */
  getLdapUsers: (params) => {
    return request.get(`${API_BASE_URL}/ldap-users/`, { params });
  },

  /**
   * 获取单个LDAP用户详情
   * @param {Number} userId - 用户ID
   * @returns {Promise} - API响应
   */
  getLdapUser: (userId) => {
    return request.get(`${API_BASE_URL}/ldap-users/${userId}`);
  },

  /**
   * 创建LDAP用户
   * @param {Object} userData - 用户数据
   * @returns {Promise} - API响应
   */
  createLdapUser: (userData) => {
    return request.post(`${API_BASE_URL}/ldap-users/`, userData);
  },

  /**
   * 更新LDAP用户
   * @param {Number} userId - 用户ID
   * @param {Object} userData - 用户数据
   * @returns {Promise} - API响应
   */
  updateLdapUser: (userId, userData) => {
    return request.put(`${API_BASE_URL}/ldap-users/${userId}`, userData);
  },

  /**
   * 删除LDAP用户
   * @param {Number} userId - 用户ID
   * @returns {Promise} - API响应
   */
  deleteLdapUser: (userId) => {
    return request.delete(`${API_BASE_URL}/ldap-users/${userId}`);
  },

  /**
   * 同步单个LDAP用户
   * @param {Number} userId - 用户ID
   * @returns {Promise} - API响应
   */
  syncLdapUser: (userId) => {
    return request.post(`${API_BASE_URL}/ldap-users/${userId}/sync`);
  },

  /**
   * 同步所有LDAP用户
   * @returns {Promise} - API响应
   */
  syncAllLdapUsers: () => {
    return request.post(`${API_BASE_URL}/ldap-users/sync-all`);
  },

  /**
   * 导入LDAP用户
   * @param {String} fileContent - CSV文件内容
   * @returns {Promise} - API响应
   */
  importLdapUsers: (fileContent) => {
    return request.post(`${API_BASE_URL}/ldap-users/import`, fileContent);
  },

  /**
   * 导出LDAP用户
   * @param {Object} filterParams - 筛选参数
   * @returns {Promise} - API响应
   */
  exportLdapUsers: (filterParams) => {
    return request.post(`${API_BASE_URL}/ldap-users/export`, filterParams);
  },

  /**
   * 获取所有角色名
   * @returns {Promise} - API响应
   */
  getLdapRoles: () => {
    return request.get(`${API_BASE_URL}/ldap-users/roles`);
  },

  /**
   * 获取所有部门名
   * @returns {Promise} - API响应
   */
  getLdapDepartments: () => {
    return request.get(`${API_BASE_URL}/ldap-users/departments`);
  }
};

export default ldapUserApi;
