import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Popconfirm, message, Card, Form, Input, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, ImportOutlined } from '@ant-design/icons';
import { getRowPermissions, deleteRowPermission } from '../../api/rowPermission';
import RowPermissionForm from './RowPermissionForm';
import RowPermissionBatchImport from './RowPermissionBatchImport';

const RowPermissionList = () => {
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

  // 获取行权限列表
  const fetchRowPermissions = async () => {
    try {
      setLoading(true);
      const params = {
        ...filters,
        page: current,
        page_size: pageSize
      };
      
      // 添加排序参数 - 只处理单个排序字段
      if (sorters && sorters.length > 0) {
        console.log('添加排序参数到请求中');
        const sorter = sorters[0]; // 只有一个排序字段
        params.sort_field = sorter.field;
        params.sort_order = sorter.order;
        console.log('完整请求参数:', params);
      }
      
      const data = await getRowPermissions(params);
      setPermissions(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('获取行权限列表失败:', error);
      message.error('获取行权限列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRowPermissions();
  }, [current, pageSize, filters, sorters]);

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
  
  // 批量导入成功后的处理
  const handleBatchImportSuccess = () => {
    setBatchImportVisible(false);
    fetchRowPermissions();
  };

  // 编辑权限
  const handleEdit = (record) => {
    setEditingPermission(record);
    setFormVisible(true);
  };

  // 删除权限
  const handleDelete = async (id) => {
    try {
      await deleteRowPermission(id);
      message.success('删除成功');
      fetchRowPermissions();
    } catch (error) {
      console.error('删除行权限失败:', error);
      message.error('删除行权限失败');
    }
  };

  // 表格翻页和排序处理
  const handleTableChange = (pagination, filters, sorter) => {
    setCurrent(pagination.current);
    setPageSize(pagination.pageSize);
    
    // 处理排序 - 只保留单个排序字段
    if (sorter && sorter.field && sorter.order) {
      // 直接设置单个排序对象
      setSorters([{ field: sorter.field, order: sorter.order }]);
      console.log('排序参数:', { field: sorter.field, order: sorter.order });
    } else {
      // 如果没有排序，清空排序状态
      setSorters([]);
      console.log('清空排序参数');
    }
  };

  // 表单提交成功后的处理
  const handleFormSuccess = () => {
    setFormVisible(false);
    fetchRowPermissions();
  };

  // 表格列定义
  const columns = [
    {
      title: '数据库名',
      dataIndex: 'db_name',
      key: 'db_name',
      sorter: true,
    },
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
      sorter: true,
    },
    {
      title: '行过滤条件',
      dataIndex: 'row_filter',
      key: 'row_filter',
      ellipsis: true,
      sorter: true,
    },
    {
      title: '用户名',
      dataIndex: 'user_name',
      key: 'user_name',
      sorter: true,
    },
    {
      title: '角色名',
      dataIndex: 'role_name',
      key: 'role_name',
      sorter: true,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      render: (text) => new Date(text).toLocaleString(),
      sorter: true,
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
      <Card title="行权限管理" style={{ marginBottom: 16 }}>
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
              添加行权限
            </Button>
            <Button
              type="primary"
              icon={<ImportOutlined />}
              onClick={handleBatchImport}
            >
              批量导入
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
        <RowPermissionForm
          visible={formVisible}
          onCancel={() => setFormVisible(false)}
          onSuccess={handleFormSuccess}
          initialValues={editingPermission}
        />
      )}
      
      {batchImportVisible && (
        <RowPermissionBatchImport
          visible={batchImportVisible}
          onCancel={() => setBatchImportVisible(false)}
          onSuccess={handleBatchImportSuccess}
        />
      )}
    </>
  );
};

export default RowPermissionList;
