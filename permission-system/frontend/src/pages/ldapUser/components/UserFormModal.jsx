import React, { useEffect } from 'react';
import { Modal, Form, Input, Select, InputNumber, Button } from 'antd';

/**
 * LDAP用户表单模态框组件
 * 
 * @param {Object} props - 组件属性
 * @param {boolean} props.visible - 模态框是否可见
 * @param {Function} props.onClose - 关闭模态框的回调函数
 * @param {Function} props.onSubmit - 表单提交的回调函数
 * @param {Object} props.user - 当前正在编辑的用户，为null时表示新增用户
 * @param {Array} props.roles - 角色列表
 * @param {Array} props.departments - 部门列表
 */
const UserFormModal = ({ visible, onClose, onSubmit, user, roles, departments }) => {
  const [form] = Form.useForm();
  const isEditing = !!user;

  // 当用户数据变化时重置表单
  useEffect(() => {
    if (visible) {
      if (user) {
        form.setFieldsValue({
          username: user.username,
          // 将逗号分隔的字符串转换为数组以适应多选框
          role_name: user.role_name ? user.role_name.split(',') : [],
          department_name: user.department_name ? user.department_name.split(',') : [],
          hdfs_quota: user.hdfs_quota,
          description: user.description,
        });
      } else {
        form.resetFields();
      }
    }
  }, [visible, user, form]);

  // 处理表单提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      // 将多选数组转换为逗号分隔的字符串
      const processedValues = {
        ...values,
        role_name: values.role_name.join(','),
        department_name: values.department_name.join(','),
      };
      onSubmit(processedValues);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  return (
    <Modal
      title={isEditing ? '编辑用户' : '新增用户'}
      visible={visible}
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
        initialValues={{
          hdfs_quota: 100,
        }}
      >
        <Form.Item
          name="username"
          label="用户名"
          rules={[
            { required: true, message: '请输入用户名' },
            { max: 50, message: '用户名最多50个字符' },
          ]}
          tooltip="用户的登录名，创建后不可更改"
        >
          <Input disabled={isEditing} placeholder="请输入用户名" />
        </Form.Item>

        {/* 新增用户时不需要密码输入字段，密码将由系统自动生成 */}
        {!isEditing && (
          <div className="ant-form-item-explain">
            <span style={{ color: '#1890ff' }}>注意：密码将自动生成，创建成功后显示</span>
          </div>
        )}

        {isEditing && (
          <Form.Item
            name="password"
            label="密码"
            tooltip="如需修改密码请输入新密码，留空则不修改"
          >
            <Input.Password placeholder="输入新密码，留空则不修改" />
          </Form.Item>
        )}

        <Form.Item
          name="role_name"
          label="角色名"
          rules={[{ required: true, message: '请选择角色' }]}
          tooltip="用户的角色，决定用户的权限范围"
        >
          <Select 
            mode="multiple"
            placeholder="请选择角色（可多选）"
            dropdownClassName="custom-dropdown-menu"
          >
            {roles.map((role) => (
              <Select.Option key={role} value={role}>
                {role}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="department_name"
          label="部门名"
          rules={[{ required: true, message: '请选择部门' }]}
          tooltip="用户所属的部门"
        >
          <Select 
            mode="multiple"
            placeholder="请选择部门（可多选）"
            dropdownClassName="custom-dropdown-menu"
          >
            {departments.map((dept) => (
              <Select.Option key={dept} value={dept}>
                {dept}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="hdfs_quota"
          label="HDFS配额(GB)"
          rules={[
            { required: true, message: '请输入HDFS配额' },
            { type: 'number', min: 1, message: '配额必须大于0' },
          ]}
          tooltip="用户的HDFS存储空间配额，单位为GB"
        >
          <InputNumber min={1} placeholder="请输入配额" style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          name="description"
          label="描述"
          tooltip="关于该用户的补充说明"
        >
          <Input.TextArea rows={4} placeholder="请输入描述信息" />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default UserFormModal;
