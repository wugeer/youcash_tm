import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Input, Space, Form, 
  message, Popconfirm, Select, InputNumber, 
  Tooltip, Card, Divider 
} from 'antd';
import { 
  PlusOutlined, DeleteOutlined, EditOutlined, 
  SyncOutlined, UploadOutlined, DownloadOutlined,
  SearchOutlined, ReloadOutlined 
} from '@ant-design/icons';
import ldapUserApi from '../../api/ldapUserApi';
import roleApi from '../../api/roleApi';
import departmentApi from '../../api/departmentApi';
import UserFormModal from './components/UserFormModal';
import ImportModal from './components/ImportModal';

/**
 * LDAP用户管理页面
 */
const LdapUserPage = () => {
  // 状态定义
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [sortField, setSortField] = useState('');
  const [sortOrder, setSortOrder] = useState('');
  const [formModalVisible, setFormModalVisible] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [roles, setRoles] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [syncingAll, setSyncingAll] = useState(false);

  // 筛选条件
  const [filters, setFilters] = useState({
    username: '',
    role_name: '',
    department_name: '',
    hdfs_quota_min: null,
    hdfs_quota_max: null,
  });

  // 缓存上次请求参数，用于去重
  const lastRequestRef = React.useRef('');
  
  // 获取用户列表数据
  const fetchUsers = async () => {
    // 构建当前请求参数
    const params = {
      ...filters,
      page: currentPage,
      page_size: pageSize,
      order_by: sortField,
      order_desc: sortOrder === 'descend',
    };
    
    // 生成参数字符串用于比较
    const paramsString = JSON.stringify(params);
    
    // 如果上次请求参数相同，则不重复请求
    if (paramsString === lastRequestRef.current) {
      console.log('请求参数相同，跳过重复请求');
      return;
    }
    
    // 更新上次请求参数
    lastRequestRef.current = paramsString;
    
    setLoading(true);
    try {
      const response = await ldapUserApi.getLdapUsers(params);
      setUsers(response.items);
      setTotal(response.total);
    } catch (error) {
      message.error('获取用户列表数据失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 获取预设的角色列表
  const fetchRoles = async () => {
    try {
      const response = await roleApi.getRoles();
      if (response && Array.isArray(response)) {
        // 从角色对象中提取角色名
        const roleNames = response.map(role => role.name);
        setRoles(roleNames);
      } else {
        // 如果API返回格式不符预期，尝试旧API
        const response = await ldapUserApi.getLdapRoles();
        if (response && response.roles) {
          setRoles(response.roles);
        }
      }
    } catch (error) {
      console.error('获取预设角色列表失败:', error);
      // 失败时尝试旧API
      try {
        const response = await ldapUserApi.getLdapRoles();
        if (response && response.roles) {
          setRoles(response.roles);
        }
      } catch (fallbackError) {
        console.error('通过备选API获取角色列表也失败:', fallbackError);
      }
    }
  };

  // 获取预设的部门列表
  const fetchDepartments = async () => {
    try {
      const response = await departmentApi.getDepartments();
      if (response && Array.isArray(response)) {
        // 从部门对象中提取部门名
        const departmentNames = response.map(dept => dept.name);
        setDepartments(departmentNames);
      } else {
        // 如果API返回格式不符预期，尝试旧API
        const response = await ldapUserApi.getLdapDepartments();
        if (response && response.departments) {
          setDepartments(response.departments);
        }
      }
    } catch (error) {
      console.error('获取预设部门列表失败:', error);
      // 失败时尝试旧API
      try {
        const response = await ldapUserApi.getLdapDepartments();
        if (response && response.departments) {
          setDepartments(response.departments);
        }
      } catch (fallbackError) {
        console.error('通过备选API获取部门列表也失败:', fallbackError);
      }
    }
  };

  // 获取用户数据的钩子
  useEffect(() => {
    fetchUsers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentPage, pageSize, sortField, sortOrder]);
  
  // 初始化时获取预设的角色和部门数据
  useEffect(() => {
    fetchRoles();
    fetchDepartments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 处理表格变化事件
  const handleTableChange = (pagination, filters, sorter) => {
    setCurrentPage(pagination.current);
    setPageSize(pagination.pageSize);
    
    // 更新排序条件
    if (sorter.field) {
      setSortField(sorter.field);
      setSortOrder(sorter.order);
    }
  };

  // 处理搜索表单提交
  const handleSearch = () => {
    setCurrentPage(1); // 重置到第一页
    fetchUsers();
  };

  // 重置搜索条件
  const handleReset = () => {
    // 定义重置后的过滤条件
    const resetFilters = {
      username: '',
      role_name: '',
      department_name: '',
      hdfs_quota_min: null,
      hdfs_quota_max: null,
    };
    
    // 更新状态
    setFilters(resetFilters);
    setCurrentPage(1);
    setSortField('');
    setSortOrder('');
    
    // 强制使上一次请求参数为空，确保不会跳过请求
    lastRequestRef.current = '';
    
    // 使用最新的重置参数直接查询
    const params = {
      ...resetFilters,
      page: 1,
      page_size: pageSize,
      order_by: '',
      order_desc: false,
    };
    
    setLoading(true);
    ldapUserApi.getLdapUsers(params)
      .then(response => {
        setUsers(response.items);
        setTotal(response.total);
      })
      .catch(error => {
        message.error('获取用户列表数据失败: ' + error.message);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  // 打开新增用户表单
  const openAddUserModal = () => {
    setCurrentUser(null);
    setFormModalVisible(true);
  };

  // 打开编辑用户表单
  const openEditUserModal = (user) => {
    setCurrentUser(user);
    setFormModalVisible(true);
  };

  // 处理表单提交
  const handleFormSubmit = async (values) => {
    try {
      setLoading(true);
      if (currentUser) {
        // 编辑用户
        await ldapUserApi.updateLdapUser(currentUser.id, values);
        message.success('用户更新成功');
      } else {
        // 新增用户
        const result = await ldapUserApi.createLdapUser(values);
        
        // 如果返回了自动生成的密码，显示给用户
        if (result && result.raw_password) {
          message.success(
            <div>
              <p>用户创建成功！</p>
              <p>用户名：{result.user.username}</p>
              <p>初始密码：<strong style={{ color: '#f5222d' }}>{result.raw_password}</strong> (请记住此密码)</p>
            </div>,
            10  // 显示10秒，给用户足够时间记录密码
          );
        } else {
          message.success('用户创建成功');
        }
      }
      
      // 关闭模态框并刷新数据
      setFormModalVisible(false);
      fetchUsers();
    } catch (error) {
      message.error(`操作失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 删除用户
  const handleDeleteUser = async (userId) => {
    try {
      await ldapUserApi.deleteLdapUser(userId);
      message.success('用户删除成功');
      fetchUsers(); // 重新加载数据
    } catch (error) {
      message.error('删除用户失败: ' + error.message);
    }
  };

  // 同步单个用户
  const handleSyncUser = async (userId) => {
    try {
      await ldapUserApi.syncLdapUser(userId);
      message.success('用户同步成功');
      fetchUsers(); // 重新加载数据
    } catch (error) {
      message.error('同步用户失败: ' + error.message);
    }
  };

  // 同步所有用户
  const handleSyncAllUsers = async () => {
    setSyncingAll(true);
    try {
      const response = await ldapUserApi.syncAllLdapUsers();
      message.success(`同步完成: 成功 ${response.data.success} 条，失败 ${response.data.failed} 条`);
      fetchUsers(); // 重新加载数据
    } catch (error) {
      message.error('同步所有用户失败: ' + error.message);
    } finally {
      setSyncingAll(false);
    }
  };

  // 打开导入用户模态框
  const openImportModal = () => {
    setImportModalVisible(true);
  };

  // 处理导入用户
  const handleImportUsers = async (fileContent) => {
    try {
      const response = await ldapUserApi.importLdapUsers(fileContent);
      message.success(`导入完成: 成功 ${response.data.success} 条，失败 ${response.data.failed} 条`);
      fetchUsers(); // 重新加载数据
      setImportModalVisible(false);
    } catch (error) {
      message.error('导入用户失败: ' + error.message);
    }
  };

  // 导出用户数据
  const handleExportUsers = async () => {
    try {
      const response = await ldapUserApi.exportLdapUsers(filters);
      // 创建下载链接
      const blob = new Blob([response.data.content], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ldap_users_${new Date().toISOString().slice(0, 10)}.csv`;
      link.click();
    } catch (error) {
      message.error('导出用户失败: ' + error.message);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      sorter: true,
      sortOrder: sortField === 'username' ? sortOrder : null,
    },
    {
      title: '角色名',
      dataIndex: 'role_name',
      key: 'role_name',
      sorter: true,
      sortOrder: sortField === 'role_name' ? sortOrder : null,
    },
    {
      title: '部门名',
      dataIndex: 'department_name',
      key: 'department_name',
      sorter: true,
      sortOrder: sortField === 'department_name' ? sortOrder : null,
    },
    {
      title: 'HDFS配额(GB)',
      dataIndex: 'hdfs_quota',
      key: 'hdfs_quota',
      sorter: true,
      sortOrder: sortField === 'hdfs_quota' ? sortOrder : null,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: true,
      sortOrder: sortField === 'created_at' ? sortOrder : null,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      sorter: true,
      sortOrder: sortField === 'updated_at' ? sortOrder : null,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button 
              icon={<EditOutlined />} 
              size="small" 
              onClick={() => openEditUserModal(record)} 
            />
          </Tooltip>
          <Tooltip title="同步">
            <Button 
              icon={<SyncOutlined />} 
              size="small" 
              onClick={() => handleSyncUser(record.id)} 
            />
          </Tooltip>
          <Tooltip title="删除">
            <Popconfirm
              title="确定要删除此用户吗?"
              onConfirm={() => handleDeleteUser(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button icon={<DeleteOutlined />} size="small" danger />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 渲染筛选区域
  const renderFilters = () => (
    <Card className="filter-card">
      <Form layout="inline">
        <Form.Item label="用户名">
          <Input
            placeholder="输入用户名"
            value={filters.username}
            onChange={(e) => setFilters({ ...filters, username: e.target.value })}
            allowClear
          />
        </Form.Item>
        <Form.Item label="角色名">
          <Select
            placeholder="选择角色"
            value={filters.role_name}
            onChange={(value) => setFilters({ ...filters, role_name: value })}
            style={{ width: 120 }}
            allowClear
            dropdownStyle={{ backgroundColor: '#ffffff', boxShadow: '0 3px 6px rgba(0,0,0,0.16)' }}
          >
            {roles.map((role) => (
              <Select.Option key={role} value={role}>{role}</Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item label="部门名">
          <Select
            placeholder="选择部门"
            value={filters.department_name}
            onChange={(value) => setFilters({ ...filters, department_name: value })}
            style={{ width: 120 }}
            allowClear
            dropdownStyle={{ backgroundColor: '#ffffff', boxShadow: '0 3px 6px rgba(0,0,0,0.16)' }}
          >
            {departments.map((dept) => (
              <Select.Option key={dept} value={dept}>{dept}</Select.Option>
            ))}
          </Select>
        </Form.Item>
        <Form.Item label="HDFS配额">
          <InputNumber
            placeholder="最小值"
            value={filters.hdfs_quota_min}
            onChange={(value) => setFilters({ ...filters, hdfs_quota_min: value })}
            style={{ width: 100 }}
          />
          <span style={{ margin: '0 8px' }}>-</span>
          <InputNumber
            placeholder="最大值"
            value={filters.hdfs_quota_max}
            onChange={(value) => setFilters({ ...filters, hdfs_quota_max: value })}
            style={{ width: 100 }}
          />
        </Form.Item>
        <Form.Item>
          <Button 
            type="primary" 
            onClick={handleSearch}
            icon={<SearchOutlined />}
          >
            查询
          </Button>
        </Form.Item>
        <Form.Item>
          <Button 
            onClick={handleReset}
            icon={<ReloadOutlined />}
          >
            重置
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );

  // 渲染按钮区域
  const renderActions = () => (
    <Space style={{ marginBottom: 16 }}>
      <Button 
        type="primary" 
        icon={<PlusOutlined />}
        onClick={openAddUserModal}
      >
        新增用户
      </Button>
      <Button 
        icon={<UploadOutlined />}
        onClick={openImportModal}
      >
        批量导入
      </Button>
      <Button 
        icon={<DownloadOutlined />}
        onClick={handleExportUsers}
      >
        导出
      </Button>
      <Button 
        icon={<SyncOutlined />}
        loading={syncingAll}
        onClick={handleSyncAllUsers}
      >
        全量同步
      </Button>
    </Space>
  );

  return (
    <div className="ldap-user-page">
      <h1>LDAP用户管理</h1>
      <Divider />

      {/* 筛选区域 */}
      {renderFilters()}
      
      {/* 按钮区域 */}
      {renderActions()}

      {/* 表格区域 */}
      <Table
        columns={columns}
        dataSource={users}
        rowKey="id"
        loading={loading}
        pagination={{
          current: currentPage,
          pageSize: pageSize,
          total: total,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条记录`,
        }}
        onChange={handleTableChange}
      />

      {/* 用户表单模态框 */}
      <UserFormModal
        visible={formModalVisible}
        onClose={() => setFormModalVisible(false)}
        onSubmit={handleFormSubmit}
        user={currentUser}
        roles={roles}
        departments={departments}
      />

      {/* 导入模态框 */}
      <ImportModal
        visible={importModalVisible}
        onClose={() => setImportModalVisible(false)}
        onImport={handleImportUsers}
      />
    </div>
  );
};

export default LdapUserPage;
