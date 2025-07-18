import React, { useEffect, useState } from 'react';
import { Modal, Form, Input, Button, message } from 'antd';
import { createRowPermission, updateRowPermission } from '../../api/rowPermission';

const { TextArea } = Input;

const RowPermissionForm = ({ visible, onCancel, onSuccess, initialValues }) => {
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
        await updateRowPermission(initialValues.id, values);
        message.success('更新行权限成功');
      } else {
        await createRowPermission(values);
        message.success('创建行权限成功');
      }

      onSuccess();
    } catch (error) {
      console.error('表单提交失败:', error);
      // 当表单验证失败时，Antd会自动在UI上显示错误信息，我们不需要做任何事。
      // 当API调用失败时，错误信息会由request.js中的全局拦截器来显示。
      // 因此，这里的catch块只需要记录错误即可，无需弹出message。
      if (error.errorFields) {
        return; // 是表单验证错误，直接返回
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={isEditing ? '编辑行权限' : '添加行权限'}
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
          name="row_filter"
          label="行过滤条件"
          rules={[{ required: true, message: '请输入行过滤条件' }]}
        >
          <TextArea
            placeholder="请输入SQL格式的行过滤条件，例如: age > 18 AND department = 'IT'"
            autoSize={{ minRows: 3, maxRows: 6 }}
          />
        </Form.Item>

        <Form.Item
          name="user_name"
          label="用户名"
          dependencies={['role_name']}
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value && !getFieldValue('role_name')) {
                  return Promise.reject(new Error('用户名和角色名至少需要填写一个'));
                }
                return Promise.resolve();
              },
            }),
          ]}
        >
          <Input placeholder="请输入用户名" />
        </Form.Item>

        <Form.Item
          name="role_name"
          label="角色名"
          dependencies={['user_name']}
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value && !getFieldValue('user_name')) {
                  return Promise.reject(new Error('用户名和角色名至少需要填写一个'));
                }
                return Promise.resolve();
              },
            }),
          ]}
        >
          <Input placeholder="请输入角色名" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default RowPermissionForm;
