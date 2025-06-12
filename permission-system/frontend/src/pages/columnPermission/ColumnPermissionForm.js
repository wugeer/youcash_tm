import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Button, message, Select } from 'antd';
import { createColumnPermission, updateColumnPermission } from '../../api/columnPermission';

const { Option } = Select;

const ColumnPermissionForm = ({ visible, onCancel, onSuccess, initialValues }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const isEditing = !!initialValues;

  // 脱敏类型选项
  const maskTypeOptions = [
    { label: '手机号', value: '手机号' },
    { label: '身份证', value: '身份证' },
    { label: '银行卡号', value: '银行卡号' },
    { label: '座机号', value: '座机号' },
    { label: '姓名', value: '姓名' },
    { label: '原文', value: '原文' },
  ];

  useEffect(() => {
    if (visible && initialValues) {
      form.setFieldsValue(initialValues);
    } else {
      form.resetFields();
    }
  }, [visible, initialValues, form]);

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      if (isEditing) {
        await updateColumnPermission(initialValues.id, values);
        message.success('更新字段权限成功');
      } else {
        await createColumnPermission(values);
        message.success('创建字段权限成功');
      }

      onSuccess();
    } catch (error) {
      console.error('表单提交失败:', error);
      if (error.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(isEditing ? '更新字段权限失败' : '创建字段权限失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={isEditing ? '编辑字段权限' : '添加字段权限'}
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          保存
        </Button>,
      ]}
      maskClosable={false}
    >
      <Form
        form={form}
        layout="vertical"
      >
        <Form.Item
          name="db_name"
          label="数据库名"
          rules={[{ required: true, message: '请输入数据库名' }]}
        >
          <Input placeholder="请输入数据库名" />
        </Form.Item>

        <Form.Item
          name="table_name"
          label="表名"
          rules={[{ required: true, message: '请输入表名' }]}
        >
          <Input placeholder="请输入表名" />
        </Form.Item>

        <Form.Item
          name="col_name"
          label="字段名"
          rules={[{ required: true, message: '请输入字段名' }]}
        >
          <Input placeholder="请输入字段名" />
        </Form.Item>

        <Form.Item
          name="mask_type"
          label="脱敏类型"
          rules={[{ required: true, message: '请选择脱敏类型' }]}
        >
          <Select placeholder="请选择脱敏类型">
            {maskTypeOptions.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="user_name"
          label="用户名"
          rules={[{ required: true, message: '请输入用户名' }]}
        >
          <Input placeholder="请输入用户名" />
        </Form.Item>

        <Form.Item
          name="role_name"
          label="角色名"
          rules={[{ required: true, message: '请输入角色名' }]}
        >
          <Input placeholder="请输入角色名" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default ColumnPermissionForm;
