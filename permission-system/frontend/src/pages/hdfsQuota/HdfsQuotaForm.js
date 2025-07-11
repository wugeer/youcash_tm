import React, { useEffect } from 'react';
import { Modal, Form, Input, InputNumber, message } from 'antd';
import { createHdfsQuota, updateHdfsQuota } from '../../api/hdfsQuota';

const HdfsQuotaForm = ({ visible, onCancel, onSuccess, initialValues }) => {
  const [form] = Form.useForm();
  const isEdit = !!initialValues;

  // 当初始值变化时重置表单
  useEffect(() => {
    if (visible) {
      form.resetFields();
      if (initialValues) {
        form.setFieldsValue(initialValues);
      }
    }
  }, [visible, initialValues, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (isEdit) {
        await updateHdfsQuota(initialValues.id, values);
        message.success('更新HDFS配额成功');
      } else {
        await createHdfsQuota(values);
        message.success('创建HDFS配额成功');
      }

      onSuccess();
    } catch (error) {
      console.error('表单提交失败:', error);
      const errorMsg = error.response?.data?.detail || '操作失败，请重试';
      message.error(errorMsg);
    }
  };

  return (
    <Modal
      title={isEdit ? '编辑HDFS配额' : '添加HDFS配额'}
      visible={visible}
      onCancel={onCancel}
      onOk={handleSubmit}
      okText="确定"
      cancelText="取消"
      maskClosable={false}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={initialValues || {}}
      >
        <Form.Item
          name="db_name"
          label="数据库名"
          rules={[
            { required: true, message: '请输入数据库名' },
            { max: 100, message: '数据库名不能超过100个字符' }
          ]}
        >
          <Input placeholder="请输入数据库名" disabled={isEdit} />
        </Form.Item>

        <Form.Item
          name="hdfs_quota"
          label="HDFS配额(GB)"
          rules={[
            { required: true, message: '请输入HDFS配额' },
            { type: 'number', min: 0.1, message: '配额必须大于0' }
          ]}
        >
          <InputNumber
            placeholder="请输入HDFS配额"
            style={{ width: '100%' }}
            step={1}
            precision={2}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default HdfsQuotaForm;
