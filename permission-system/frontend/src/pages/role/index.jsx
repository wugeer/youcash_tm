import React, { useState, useEffect } from 'react';
import { 
  Table, Button, Input, Space, Form, 
  message, Popconfirm, Card, Divider 
} from 'antd';
import { 
  PlusOutlined, DeleteOutlined, EditOutlined,
  SearchOutlined, ReloadOutlined 
} from '@ant-design/icons';
import roleApi from '../../api/roleApi';
import RoleFormModal from './components/RoleFormModal';

/**
 * 角色管理页面
 */
const RolePage = () => {
  // 状态定义
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [sortField, setSortField] = useState('');
  const [sortOrder, setSortOrder] = useState('');
  const [formModalVisible, setFormModalVisible] = useState(false);
  const [currentRole, setCurrentRole] = useState(null);

  // 筛选条件
  const [filters, setFilters] = useState({
    name: '', // 使用name字段与后端API一致
  });

  // 缓存上次请求参数，用于去重
  const lastRequestRef = React.useRef('');
  
  // 获取角色列表数据
  const fetchRoles = async (forceRefresh = false) => {
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
    
    // 如果不是强制刷新且上次请求参数相同，则不重复请求
    if (!forceRefresh && paramsString === lastRequestRef.current) {
      console.log('请求参数相同，跳过重复请求');
      return;
    }
    
    // 更新上次请求参数
    lastRequestRef.current = paramsString;
    
    setLoading(true);
    try {
      const response = await roleApi.getRoles(params);
      if (Array.isArray(response)) {
        setRoles(response);
        setTotal(response.length); // 如果API没有返回总数，则使用当前数组长度
      } else if (response && response.items) {
        setRoles(response.items);
        setTotal(response.total || response.items.length);
      } else {
        setRoles([]);
        setTotal(0);
      }
    } catch (error) {
      message.error('获取角色列表数据失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 页面加载时获取数据
  useEffect(() => {
    fetchRoles();
  }, [currentPage, pageSize, sortField, sortOrder, filters]);

  // 处理表格变化事件
  const handleTableChange = (pagination, filters, sorter) => {
    setCurrentPage(pagination.current);
    setPageSize(pagination.pageSize);
    
    if (sorter && sorter.field) {
      setSortField(sorter.field);
      setSortOrder(sorter.order);
    }
  };

  // 处理搜索表单提交
  const handleSearch = () => {
    setCurrentPage(1);
    fetchRoles(true); // 强制刷新
  };

  // 重置搜索条件
  const handleReset = () => {
    setFilters({
      name: '',
    });
    setCurrentPage(1);
    setSortField('');
    setSortOrder('');
    // 状态更新后，useEffect将自动触发fetchRoles
  };

  // 打开新增角色表单
  const openAddRoleModal = () => {
    setCurrentRole(null);
    setFormModalVisible(true);
  };

  // 打开编辑角色表单
  const openEditRoleModal = (role) => {
    setCurrentRole(role);
    setFormModalVisible(true);
  };

  // 处理表单提交
  const handleFormSubmit = async (values) => {
    try {
      if (currentRole) {
        // 编辑现有角色
        await roleApi.updateRole(currentRole.id, values);
        message.success('角色更新成功');
        
        // 关闭模态框并刷新数据
        setFormModalVisible(false);
        fetchRoles(true);
      } else {
        // 创建新角色
        await roleApi.createRole(values);
        message.success('角色创建成功');
        
        // 关闭模态框并刷新数据
        setFormModalVisible(false);
        fetchRoles(true);
      }
    } catch (error) {
      // 提取错误信息，避免显示generic错误
      // 注意：此处不关闭模态框，让用户可以修改后重试
      const errorMessage = error.response?.data?.detail || error.message || '未知错误';
      message.error(`操作失败: ${errorMessage}`);
      
      // 防止全局Modal和message同时显示错误，阻止错误冒泡
      return Promise.resolve(); // 阻止错误继续传播到全局处理
    }
  };

  // 删除角色
  const handleDeleteRole = async (roleId) => {
    try {
      await roleApi.deleteRole(roleId);
      message.success('角色删除成功');
      fetchRoles(true);
    } catch (error) {
      message.error('删除失败: ' + error.message);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '角色名称',
      dataIndex: 'name', // 使用name字段与后端API返回数据一致
      key: 'name',
      sorter: true,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      sorter: true,
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="text" 
            icon={<EditOutlined />} 
            onClick={() => openEditRoleModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除该角色吗？"
            description="删除后将无法恢复，关联的用户权限将受到影响。"
            onConfirm={() => handleDeleteRole(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="text" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 渲染筛选区域
  const renderFilters = () => (
    <Card className="filter-card">
      <Form layout="inline">
        <Form.Item label="角色名称">
          <Input
            placeholder="输入角色名称"
            value={filters.name}
            onChange={(e) => setFilters({ ...filters, name: e.target.value })}
            allowClear
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
        onClick={openAddRoleModal}
      >
        新增角色
      </Button>
    </Space>
  );

  return (
    <div className="role-page">
      <h1>角色管理</h1>
      <Divider />

      {/* 筛选区域 */}
      {renderFilters()}
      
      {/* 按钮区域 */}
      {renderActions()}

      {/* 表格区域 */}
      <Table
        columns={columns}
        dataSource={roles}
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

      {/* 角色表单模态框 */}
      <RoleFormModal
        visible={formModalVisible}
        onClose={() => setFormModalVisible(false)}
        onSubmit={handleFormSubmit}
        role={currentRole}
      />
    </div>
  );
};

export default RolePage;
