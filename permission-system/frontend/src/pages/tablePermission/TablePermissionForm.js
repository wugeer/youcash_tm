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

  // 自定义校验：用户名和角色名至少填一个
  const validateUserOrRole = (_, value) => {
    if (value || form.getFieldValue('role_name')) {
      return Promise.resolve();
    }
    return Promise.reject(new Error('用户名和角色名至少填一个'));
  };

  const validateRoleOrUser = (_, value) => {
    if (value || form.getFieldValue('user_name')) {
      return Promise.resolve();
    }
    return Promise.reject(new Error('用户名和角色名至少填一个'));
  };

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
        // Ant Design form validation error
        return;
      }
      let errorMessage = isEditing ? '更新表权限失败' : '创建表权限失败';
      if (error.response && error.response.data && error.response.data.detail) {
        const detail = error.response.data.detail;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail) && detail.length > 0 && typeof detail[0] === 'object' && detail[0] !== null && detail[0].msg) {
          // Pydantic validation errors often come as an array of objects like [{loc: [field], msg: '', type: ''}]
          errorMessage = detail.map(err => `${err.loc.join('.')} - ${err.msg}`).join('; ');
        } else if (typeof detail === 'object' && detail !== null && detail.msg) {
          // Sometimes it might be a single error object
          errorMessage = detail.msg;
        }
      }
      message.error(errorMessage);
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
          rules={[{ validator: validateUserOrRole }]} 
        >
          <Input placeholder="请输入用户名" />
        </Form.Item>

        <Form.Item
          name="role_name"
          label="角色名"
          rules={[{ validator: validateRoleOrUser }]} 
        >
          <Input placeholder="请输入角色名" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default TablePermissionForm;
