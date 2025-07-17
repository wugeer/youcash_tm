import React, { useState } from 'react';
import { Modal, Form, Input, Button, message, Alert, Typography } from 'antd';
import { batchCreateTablePermissions } from '../../api/tablePermission';

const { TextArea } = Input;
const { Paragraph, Text } = Typography;

const TablePermissionBatchImport = ({ visible, onCancel, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [parseError, setParseError] = useState(null);

  // 解析输入的多行文本
  const parseInputData = (text) => {
    if (!text || !text.trim()) {
      return { success: false, error: '请输入数据' };
    }

    const lines = text.trim().split('\n').filter(line => line.trim());
    if (lines.length === 0) {
      return { success: false, error: '没有有效的数据行' };
    }

    const parsedData = [];
    const errors = [];

    lines.forEach((line, index) => {
      // 使用制表符或逗号分隔
      const parts = line.split(/[,\t]+/).map(part => part.trim());
      
      // 检查每行至少有2个字段（数据库名和表名是必须的）
      if (parts.length < 2) {
        errors.push(`第 ${index + 1} 行: 格式不正确，至少需要数据库名和表名`);
        return;
      }

      // 解析字段
      const [db_name, table_name, user_names = '', role_names = ''] = parts;
      
      // 验证必填字段
      if (!db_name) {
        errors.push(`第 ${index + 1} 行: 数据库名不能为空`);
        return;
      }
      
      if (!table_name) {
        errors.push(`第 ${index + 1} 行: 表名不能为空`);
        return;
      }
      
      // 验证用户名和角色名至少有一个
      if (!user_names && !role_names) {
        errors.push(`第 ${index + 1} 行: 用户名和角色名至少填一个`);
        return;
      }
      
      // 处理多用户和多角色（使用+分隔）
      const userNameList = user_names ? user_names.split('+').map(name => name.trim()).filter(name => name) : [];
      const roleNameList = role_names ? role_names.split('+').map(name => name.trim()).filter(name => name) : [];

      // 如果用户名和角色名都为空列表，说明格式不对
      if (userNameList.length === 0 && roleNameList.length === 0) {
        errors.push(`第 ${index + 1} 行: 用户名和角色名至少填一个`);
        return;
      }

      // 一一对应方式处理用户名和角色名
      if (userNameList.length === 0) {
        // 只有角色名，没有用户名
        for (const roleName of roleNameList) {
          parsedData.push({
            db_name,
            table_name,
            user_name: '',
            role_name: roleName
          });
        }
      } else if (roleNameList.length === 0) {
        // 只有用户名，没有角色名
        for (const userName of userNameList) {
          parsedData.push({
            db_name,
            table_name,
            user_name: userName,
            role_name: ''
          });
        }
      } else {
        // 既有用户名也有角色名，一一对应处理
        const maxLength = Math.max(userNameList.length, roleNameList.length);
        
        for (let i = 0; i < maxLength; i++) {
          // 获取当前索引的用户名和角色名，如果超出范围则为空
          const userName = i < userNameList.length ? userNameList[i] : '';
          const roleName = i < roleNameList.length ? roleNameList[i] : '';
          
          // 如果当前位置有用户名或角色名，则添加一条记录
          if (userName || roleName) {
            parsedData.push({
              db_name,
              table_name,
              user_name: userName,
              role_name: roleName
            });
          }
        }
      }
    });

    if (errors.length > 0) {
      return { success: false, error: errors.join('\n') };
    }

    return { success: true, data: parsedData };
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const parseResult = parseInputData(values.batchData);
      
      if (!parseResult.success) {
        setParseError(parseResult.error);
        return;
      }
      
      setParseError(null);
      setLoading(true);

      // 调用批量创建API - 使用正确的格式包装数据
      await batchCreateTablePermissions({
        items: parseResult.data,
        batch_sync: false // 默认逐条同步
      });
      message.success(`成功导入 ${parseResult.data.length} 条表权限记录`);
      form.resetFields();
      onSuccess();
    } catch (error) {
      console.error('批量导入失败:', error);
      let errorMessage = '批量导入失败';
      
      if (error.response && error.response.data) {
        if (error.response.data.detail) {
          const detail = error.response.data.detail;
          if (typeof detail === 'string') {
            errorMessage = detail;
          } else if (Array.isArray(detail) && detail.length > 0) {
            errorMessage = detail.map((err, index) => 
              `第 ${index + 1} 条记录: ${err.msg || JSON.stringify(err)}`
            ).join('\n');
          }
        }
      }
      
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="批量导入表权限"
      open={visible}
      onCancel={onCancel}
      width={700}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button key="submit" type="primary" loading={loading} onClick={handleSubmit}>
          导入
        </Button>,
      ]}
      maskClosable={false}
    >
      <Alert
        message="格式说明"
        description={
          <div>
            <Paragraph>
              请按照以下格式输入数据，每行一条记录：
            </Paragraph>
            <Paragraph>
              <Text code>数据库名,表名,用户名1+用户名2+...,角色名1+角色名2+...</Text>
            </Paragraph>
            <Paragraph>
              说明：
              <ul>
                <li>字段之间使用逗号或制表符分隔</li>
                <li>数据库名和表名为必填项</li>
                <li>用户名和角色名至少填写一个</li>
                <li>多个用户名或角色名之间使用加号(+)分隔</li>
                <li>示例：<Text code>test_db,users,admin+guest,</Text> 或 <Text code>test_db,orders,user1,manager+viewer</Text></li>
                <li>多用户多角色将一一对应创建权限记录，例如 <Text code>test_db,users,admin+guest,manager+viewer</Text> 会创建2条记录：admin-manager和guest-viewer</li>
                <li>如果用户数量和角色数量不同，多出的部分将单独创建权限记录</li>
              </ul>
            </Paragraph>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      {parseError && (
        <Alert
          message="解析错误"
          description={<pre style={{ whiteSpace: 'pre-wrap' }}>{parseError}</pre>}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Form form={form} layout="vertical">
        <Form.Item
          name="batchData"
          rules={[{ required: true, message: '请输入批量导入数据' }]}
        >
          <TextArea
            placeholder="请输入批量导入数据，每行一条记录"
            autoSize={{ minRows: 10, maxRows: 20 }}
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default TablePermissionBatchImport;
