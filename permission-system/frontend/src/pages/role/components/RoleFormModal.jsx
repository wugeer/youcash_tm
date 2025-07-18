import React, { useEffect } from 'react';
import { Modal, Form, Input, Button } from 'antd';

/**
 * 角色表单模态框组件
 * 
 * @param {Object} props - 组件属性
 * @param {boolean} props.visible - 模态框是否可见
 * @param {Function} props.onClose - 关闭模态框的回调函数
 * @param {Function} props.onSubmit - 表单提交的回调函数
 * @param {Object} props.role - 当前正在编辑的角色，为null时表示新增角色
 */
const RoleFormModal = ({ visible, onClose, onSubmit, role }) => {
  const [form] = Form.useForm();
  const isEditing = !!role;

  // 当角色数据变化时重置表单
  useEffect(() => {
    if (visible) {
      if (role) {
        form.setFieldsValue({
          name: role.name, // 直接使用name字段，与后端返回匹配
          description: role.description,
        });
      } else {
        form.resetFields();
      }
    }
  }, [visible, role, form]);

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      onSubmit(values);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  return (
    <Modal
      title={isEditing ? '编辑角色' : '新增角色'}
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button key="submit" type="primary" onClick={handleSubmit}>
          保存
        </Button>,
      ]}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
      >
        <Form.Item
          name="name"
          label="角色名称"
          rules={[
            { required: true, message: '请输入角色名称' },
            { max: 50, message: '角色名称最多50个字符' },
          ]}
          tooltip="角色的名称，必须唯一"
        >
          <Input placeholder="请输入角色名称" />
        </Form.Item>

        <Form.Item
          name="description"
          label="描述"
          tooltip="关于该角色的补充说明"
        >
          <Input.TextArea rows={4} placeholder="请输入角色描述信息" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default RoleFormModal;
