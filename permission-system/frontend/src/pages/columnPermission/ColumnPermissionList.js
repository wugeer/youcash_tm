import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Popconfirm, message, Card, Form, Input, Row, Col, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { getColumnPermissions, deleteColumnPermission } from '../../api/columnPermission';
import ColumnPermissionForm from './ColumnPermissionForm';

const { Option } = Select;

const ColumnPermissionList = () => {
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [current, setCurrent] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState({});
  const [formVisible, setFormVisible] = useState(false);
  const [editingPermission, setEditingPermission] = useState(null);
  const [form] = Form.useForm();

  // 获取字段权限列表
  const fetchColumnPermissions = async () => {
    try {
      setLoading(true);
      const params = {
        ...filters,
        page: current,
        page_size: pageSize
      };
      const data = await getColumnPermissions(params);
      setPermissions(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('获取字段权限列表失败:', error);
      message.error('获取字段权限列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchColumnPermissions();
  }, [current, pageSize, filters]);

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

  // 编辑权限
  const handleEdit = (record) => {
    setEditingPermission(record);
    setFormVisible(true);
  };

  // 删除权限
  const handleDelete = async (id) => {
    try {
      await deleteColumnPermission(id);
      message.success('删除成功');
      fetchColumnPermissions();
    } catch (error) {
      console.error('删除字段权限失败:', error);
      message.error('删除字段权限失败');
    }
  };

  // 表格翻页处理
  const handleTableChange = (pagination) => {
    setCurrent(pagination.current);
    setPageSize(pagination.pageSize);
  };

  // 表单提交成功后的处理
  const handleFormSuccess = () => {
    setFormVisible(false);
    fetchColumnPermissions();
  };

  // 表格列定义
  const columns = [
    {
      title: '数据库名',
      dataIndex: 'db_name',
      key: 'db_name',
    },
    {
      title: '表名',
      dataIndex: 'table_name',
      key: 'table_name',
    },
    {
      title: '字段名',
      dataIndex: 'col_name',
      key: 'col_name',
    },
    {
      title: '脱敏类型',
      dataIndex: 'mask_type',
      key: 'mask_type',
    },
    {
      title: '用户名',
      dataIndex: 'user_name',
      key: 'user_name',
    },
    {
      title: '角色名',
      dataIndex: 'role_name',
      key: 'role_name',
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      render: (text) => new Date(text).toLocaleString(),
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

  // 脱敏类型选项
  const maskTypeOptions = [
    { label: '手机号', value: '手机号' },
    { label: '身份证', value: '身份证' },
    { label: '银行卡号', value: '银行卡号' },
    { label: '座机号', value: '座机号' },
    { label: '姓名', value: '姓名' },
    { label: '原文', value: '原文' },
  ];

  return (
    <>
      <Card title="字段权限管理" style={{ marginBottom: 16 }}>
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
              <Form.Item name="col_name" label="字段名">
                <Input placeholder="请输入字段名" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={6}>
              <Form.Item name="mask_type" label="脱敏类型">
                <Select placeholder="请选择脱敏类型" allowClear>
                  {maskTypeOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
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
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            添加字段权限
          </Button>
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
        <ColumnPermissionForm
          visible={formVisible}
          onCancel={() => setFormVisible(false)}
          onSuccess={handleFormSuccess}
          initialValues={editingPermission}
        />
      )}
    </>
  );
};

export default ColumnPermissionList;
