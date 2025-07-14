import React, { useState, useEffect, useCallback } from 'react';
import { 
  Table, Button, Space, Popconfirm, message, 
  Card, Form, Input, Row, Col
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, 
  UploadOutlined, SyncOutlined
} from '@ant-design/icons';
import { getHdfsQuotas, deleteHdfsQuota, syncHdfsQuotas, syncHdfsQuota } from '../../api/hdfsQuota';
import HdfsQuotaForm from './HdfsQuotaForm';
import HdfsQuotaBatchImport from './HdfsQuotaBatchImport';

const HdfsQuotaList = () => {
  const [quotas, setQuotas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [current, setCurrent] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState({});
  const [sorters, setSorters] = useState([]);
  const [formVisible, setFormVisible] = useState(false);
  const [editingQuota, setEditingQuota] = useState(null);
  const [form] = Form.useForm();
  
  // 批量导入相关状态
  const [batchImportVisible, setBatchImportVisible] = useState(false);

  // 同步中状态
  const [syncLoading, setSyncLoading] = useState(false);

  // 获取HDFS配额列表
  const fetchHdfsQuotas = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        ...filters,
        page: current,
        page_size: pageSize,
      };
      if (sorters.length > 0) {
        const firstSorter = sorters[0];
        params.sort_field = firstSorter.field;
        params.sort_order = firstSorter.order;
      }
      const data = await getHdfsQuotas(params);
      setQuotas(data.items);
      setTotal(data.total);
    } catch (error) {
      console.error('获取HDFS配额列表失败:', error);
      message.error('获取HDFS配额列表失败');
    } finally {
      setLoading(false);
    }
  }, [filters, current, pageSize, sorters]);

  useEffect(() => {
    fetchHdfsQuotas();
  }, [fetchHdfsQuotas]);

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

  // 添加新配额
  const handleAdd = () => {
    setEditingQuota(null);
    setFormVisible(true);
  };

  // 编辑配额
  const handleEdit = (record) => {
    setEditingQuota(record);
    setFormVisible(true);
  };

  // 同步HDFS配额
  const handleSync = async () => {
    try {
      setSyncLoading(true);
      await syncHdfsQuotas();
      message.success('同步成功');
      fetchHdfsQuotas();
    } catch (error) {
      console.error('同步HDFS配额失败:', error);
      message.error('同步失败');
    } finally {
      setSyncLoading(false);
    }
  };

  // 同步单行配额
  const handleSyncRow = async (id) => {
    try {
      await syncHdfsQuota(id);
      message.success('同步成功');
    } catch (error) {
      console.error('同步HDFS配额失败:', error);
      message.error('同步失败');
    }
  };

  // 删除配额
  const handleDelete = async (id) => {
    try {
      await deleteHdfsQuota(id);
      message.success('删除成功');
      fetchHdfsQuotas();
    } catch (error) {
      console.error('删除HDFS配额失败:', error);
      message.error('删除HDFS配额失败');
    }
  };

  // 表格翻页和排序处理
  const handleTableChange = (pagination, filters, sorter) => {
    setCurrent(pagination.current);
    setPageSize(pagination.pageSize);

    // 处理排序状态
    console.log('Table sorter:', sorter);
    let newSorters = [];
    
    if (sorter && sorter.field) {
      // 单列排序
      if (sorter.order) {
        newSorters = [{ field: sorter.field, order: sorter.order }];
      }
    } else if (Array.isArray(sorter) && sorter.length > 0) {
      // 多列排序
      newSorters = sorter
        .filter(s => s.order)
        .map(s => ({ field: s.field, order: s.order }));
    }
    
    console.log('Setting new sorters:', newSorters);
    setSorters(newSorters);
  };

  // 表单提交成功后的处理
  const handleFormSuccess = () => {
    setFormVisible(false);
    fetchHdfsQuotas();
  };
  
  // 显示批量导入模态框
  const showBatchImport = () => {
    setBatchImportVisible(true);
  };
  
  // 关闭批量导入模态框
  const handleBatchImportCancel = () => {
    setBatchImportVisible(false);
  };
  
  // 批量导入成功处理
  const handleBatchImportSuccess = () => {
    setBatchImportVisible(false);
    fetchHdfsQuotas();
  };

  // 表格列定义
  const columns = [
    {
      title: '数据库名',
      dataIndex: 'db_name',
      key: 'db_name',

      sorter: true,
      sortOrder: sorters.find(s => s.field === 'db_name')?.order,
    },
    {
      title: 'HDFS配额(GB)',
      dataIndex: 'hdfs_quota',
      key: 'hdfs_quota',
      sorter: true,
      sortOrder: sorters.find(s => s.field === 'hdfs_quota')?.order,
      render: (text) => text.toFixed(2),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
      sorter: true,
      sortOrder: sorters.find(s => s.field === 'created_at')?.order,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (text) => new Date(text).toLocaleString(),
      sorter: true,
      sortOrder: sorters.find(s => s.field === 'updated_at')?.order,
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
      <Card title="HDFS配额管理" style={{ marginBottom: 16 }}>
        <Form form={form} onFinish={handleSearch} layout="vertical">
          <Row gutter={16}>
            <Col xs={24} sm={12} md={8} lg={8}>
              <Form.Item name="db_name" label="数据库名">
                <Input placeholder="请输入数据库名" />
              </Form.Item>
            </Col>
            <Col xs={24} sm={12} md={16} lg={16} style={{ textAlign: 'right' }}>
              <Space style={{ marginTop: 40 }}>
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
              添加HDFS配额
            </Button>
            <Button
              type="primary"
              danger={false}
              ghost={false}
              icon={<UploadOutlined />}
              onClick={showBatchImport}
              style={{ backgroundColor: '#722ed1 !important', borderColor: '#722ed1 !important', color: '#000 !important' }}
            >
              批量导入
            </Button>
            <Button
              icon={<SyncOutlined style={{ color: '#52c41a' }} />}
              loading={syncLoading}
              onClick={handleSync}
              style={{ color: '#52c41a' }}
            >
              同步配额
            </Button>
          </Space>
        </div>
        
        <Table
          columns={columns}
          dataSource={quotas}
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
        <HdfsQuotaForm
          visible={formVisible}
          onCancel={() => setFormVisible(false)}
          onSuccess={handleFormSuccess}
          initialValues={editingQuota}
        />
      )}
      
      <HdfsQuotaBatchImport 
        visible={batchImportVisible}
        onCancel={handleBatchImportCancel}
        onSuccess={handleBatchImportSuccess}
      />
    </>
  );
};

export default HdfsQuotaList;
