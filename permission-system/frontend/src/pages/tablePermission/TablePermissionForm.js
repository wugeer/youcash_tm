import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Button, message } from 'antd';
import { createTablePermission, updateTablePermission } from '../../api/tablePermission';

const TablePermissionForm = ({ visible, onCancel, onSuccess, initialValues }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const isEditing = !!initialValues;

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
        await updateTablePermission(initialValues.id, values);
        message.success('更新表权限成功');
      } else {
        await createTablePermission(values);
        message.success('创建表权限成功');
      }

      onSuccess();
    } catch (error) {
      console.error('表单提交失败:', error);
      if (error.errorFields) {
        // 表单验证错误
        return;
      }
      message.error(isEditing ? '更新表权限失败' : '创建表权限失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={isEditing ? '编辑表权限' : '添加表权限'}
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

export default TablePermissionForm;
