import React, { useEffect } from 'react';
import { Modal, Form, Input, Button } from 'antd';

/**
 * 部门表单模态框组件
 * 
 * @param {Object} props - 组件属性
 * @param {boolean} props.visible - 模态框是否可见
 * @param {Function} props.onClose - 关闭模态框的回调函数
 * @param {Function} props.onSubmit - 表单提交的回调函数
 * @param {Object} props.department - 当前正在编辑的部门，为null时表示新增部门
 */
const DepartmentFormModal = ({ visible, onClose, onSubmit, department }) => {
  const [form] = Form.useForm();
  const isEditing = !!department;

  // 当部门数据变化时重置表单
  useEffect(() => {
    if (visible) {
      if (department) {
        form.setFieldsValue({
          name: department.name, // 直接使用name字段，与后端返回匹配
          description: department.description,
        });
      } else {
        form.resetFields();
      }
    }
  }, [visible, department, form]);

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
      title={isEditing ? '编辑部门' : '新增部门'}
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
          label="部门名称"
          rules={[
            { required: true, message: '请输入部门名称' },
            { max: 50, message: '部门名称最多50个字符' },
          ]}
          tooltip="部门的名称，必须唯一"
        >
          <Input placeholder="请输入部门名称" />
        </Form.Item>

        <Form.Item
          name="description"
          label="描述"
          tooltip="关于该部门的补充说明"
        >
          <Input.TextArea rows={4} placeholder="请输入部门描述信息" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default DepartmentFormModal;
