import React, { useState, useEffect, useCallback } from 'react';
import { Table, Button, Space, Popconfirm, message, Card, Form, Input, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, ImportOutlined, SyncOutlined } from '@ant-design/icons';
import { getTablePermissions, deleteTablePermission, syncTablePermissions, syncTablePermission } from '../../api/tablePermission';
import TablePermissionForm from './TablePermissionForm';
import TablePermissionBatchImport from './TablePermissionBatchImport';

const TablePermissionList = () => {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [current, setCurrent] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState({});
  const [sorters, setSorters] = useState([]);
  const [formVisible, setFormVisible] = useState(false);
  const [batchImportVisible, setBatchImportVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState(null);
  const [form] = Form.useForm();

  // 缓存上次请求参数，用于去重
  const lastRequestRef = React.useRef('');

  // 获取表权限列表
  const fetchTablePermissions = useCallback(async () => {
    // 构建当前请求参数
    const params = {
      ...filters,
      page: current,
      page_size: pageSize,
    };
    if (sorters.length > 0) {
      // 使用单独的参数传递排序字段和排序方向，避免复杂的JSON序列化
      const firstSorter = sorters[0]; // 暂时只处理第一个排序
      params.sort_field = firstSorter.field;
      params.sort_order = firstSorter.order;
    }
    
    // 生成参数字符串用于比较
    const paramsString = JSON.stringify(params);
    
    // 如果上次请求参数相同，则不重复请求
    if (paramsString === lastRequestRef.current) {
      console.log('请求参数相同，跳过重复请求');
      return;
    }
    
    // 更新上次请求参数
    lastRequestRef.current = paramsString;

    try {
      setLoading(true);
      const data = await getTablePermissions(params);
      setPermissions(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('获取表权限列表失败:', error);
      message.error('获取表权限列表失败');
    } finally {
      setLoading(false);
    }
  }, [filters, current, pageSize, sorters]);

  useEffect(() => {
    fetchTablePermissions();
  }, [fetchTablePermissions]);

  // 搜索处理
  const handleSearch = (values) => {
    const searchParams = {};
    for (const key in values) {
      if (values[key]) {
        searchParams[key] = values[key];
      }
    }
    setFilters(searchParams);
    setCurrent(1);
  };

  // 重置搜索
  const handleReset = () => {
    form.resetFields();
    setFilters({});
    setCurrent(1);
  };

  // 添加新权限
  const handleAdd = () => {
    setEditingPermission(null);
    setFormVisible(true);
  };
  
  // 打开批量导入模态框
  const handleBatchImport = () => {
    setBatchImportVisible(true);
  };

  // 同步表权限
  const handleSync = async () => {
    try {
      await syncTablePermissions();
      message.success('同步成功');
      fetchTablePermissions();
    } catch (error) {
      console.error('同步表权限失败:', error);
      message.error('同步失败');
    }
  };

  // 批量导入成功后的处理
  const handleBatchImportSuccess = () => {
    setBatchImportVisible(false);
    fetchTablePermissions();
  };

  // 编辑权限
  const handleEdit = (record) => {
    setEditingPermission(record);
    setFormVisible(true);
  };

  // 同步单行权限
  const handleSyncRow = async (id) => {
    try {
      await syncTablePermission(id);
      message.success('同步成功');
    } catch (error) {
      console.error('同步表权限失败:', error);
      message.error('同步失败');
    }
  };

  // 删除权限
  const handleDelete = async (id) => {
    try {
      await deleteTablePermission(id);
      message.success('删除成功');
      fetchTablePermissions();
    } catch (error) {
      console.error('删除表权限失败:', error);
      message.error('删除表权限失败');
    }
  };

  // 表格翻页处理
  const handleTableChange = (pagination, filters, sorter) => {
    setCurrent(pagination.current);
    setPageSize(pagination.pageSize);

    const sorterList = Array.isArray(sorter) ? sorter : (sorter.field ? [sorter] : []);
    const activeSorters = sorterList
      .filter(s => s.order)
      .map(s => ({ field: s.field, order: s.order }));
    
    setSorters(activeSorters);
  };

  // 表单提交成功后的处理
  const handleFormSuccess = () => {
    setFormVisible(false);
    fetchTablePermissions();
  };

  // 表格列定义
  const columns = [
    {
      title: '数据库名',
      dataIndex: 'db_name',
      key: 'db_name',
      sorter: { multiple: 1 },
    },
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
      sorter: { multiple: 2 },
    },
    {
      title: '用户名',
      dataIndex: 'user_name',
      key: 'user_name',
      sorter: { multiple: 3 },
    },
    {
      title: '角色名',
      dataIndex: 'role_name',
      key: 'role_name',
      sorter: { multiple: 4 },
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      render: (text) => new Date(text).toLocaleString(),
      sorter: true,
      sortDirections: ['ascend', 'descend'],
    },
    {
      title: '更新时间',
      dataIndex: 'update_time',
      key: 'update_time',
      render: (text) => new Date(text).toLocaleString(),
      sorter: true,
      sortDirections: ['ascend', 'descend'],
      defaultSortOrder: 'descend',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="middle">
          <Button 
            type="primary" 
            icon={<EditOutlined />} 
            size="small"
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Button 
            icon={<SyncOutlined style={{ color: '#52c41a' }} />} 
            size="small"
            onClick={() => handleSyncRow(record.id)}
            style={{ color: '#52c41a' }}
          >
            同步
          </Button>
          <Popconfirm
            title="确定要删除此项吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              danger 
              icon={<DeleteOutlined />} 
              size="small"
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Card title="表权限管理" style={{ marginBottom: 16 }}>
        <Form form={form} onFinish={handleSearch} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="db_name" label="数据库名">
                <Input placeholder="请输入数据库名" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="table_name" label="表名">
                <Input placeholder="请输入表名" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="user_name" label="用户名">
                <Input placeholder="请输入用户名" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="role_name" label="角色名">
                <Input placeholder="请输入角色名" />
              </Form.Item>
            </Col>
          </Row>
          <Row>
            <Col span={24} style={{ textAlign: 'right' }}>
              <Space>
                <Button onClick={handleReset}>重置</Button>
                <Button type="primary" htmlType="submit" icon={<SearchOutlined />}>
                  搜索
                </Button>
              </Space>
            </Col>
          </Row>
        </Form>
      </Card>

      <Card>
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAdd}
            >
              添加表权限
            </Button>
            <Button
              type="primary"
              icon={<ImportOutlined />}
              onClick={handleBatchImport}
            >
              批量导入
            </Button>
            <Button
              icon={<SyncOutlined style={{ color: '#52c41a' }} />}
              onClick={handleSync}
              style={{ color: '#52c41a' }}
            >
              同步权限
            </Button>
          </Space>
        </div>
        
        <Table
          columns={columns}
          dataSource={permissions}
          rowKey="id"
          loading={loading}
          pagination={{
            current,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          onChange={handleTableChange}
        />
      </Card>

      {formVisible && (
        <TablePermissionForm
          visible={formVisible}
          onCancel={() => setFormVisible(false)}
          onSuccess={handleFormSuccess}
          initialValues={editingPermission}
        />
      )}
      
      {batchImportVisible && (
        <TablePermissionBatchImport
          visible={batchImportVisible}
          onCancel={() => setBatchImportVisible(false)}
          onSuccess={handleBatchImportSuccess}
        />
      )}
    </>
  );
};

export default TablePermissionList;
