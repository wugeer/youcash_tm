import React, { useState } from 'react';
import { Modal, Form, Input, Button, message, Alert, Typography } from 'antd';
import { batchCreateColumnPermissions } from '../../api/columnPermission';

const { TextArea } = Input;
const { Paragraph, Text } = Typography;

const ColumnPermissionBatchImport = ({ visible, onCancel, onSuccess }) => {
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
      
      // 检查每行至少有4个字段（数据库名、表名、列名和脱敏类型是必须的）
      if (parts.length < 4) {
        errors.push(`第 ${index + 1} 行: 格式不正确，至少需要数据库名、表名、列名和脱敏类型`);
        return;
      }

      // 解析字段
      const [db_name, table_name, col_name, mask_type, user_names = '', role_names = ''] = parts;
      
      // 验证必填字段
      if (!db_name) {
        errors.push(`第 ${index + 1} 行: 数据库名不能为空`);
        return;
      }
      
      if (!table_name) {
        errors.push(`第 ${index + 1} 行: 表名不能为空`);
        return;
      }
      
      if (!col_name) {
        errors.push(`第 ${index + 1} 行: 列名不能为空`);
        return;
      }
      
      if (!mask_type) {
        errors.push(`第 ${index + 1} 行: 脱敏类型不能为空`);
        return;
      }
      
      // 验证脱敏类型
      const validMaskTypes = ['手机号', '身份证', '银行卡号', '座机号', '姓名', '原文'];
      if (!validMaskTypes.includes(mask_type)) {
        errors.push(`第 ${index + 1} 行: 脱敏类型必须是以下之一: ${validMaskTypes.join(', ')}`);
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
            col_name,
            mask_type,
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
            col_name,
            mask_type,
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
              col_name,
              mask_type,
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

      // 调用批量创建API
      await batchCreateColumnPermissions(parseResult.data);
      message.success(`成功导入 ${parseResult.data.length} 条字段权限记录`);
      form.resetFields();
      onSuccess();
    } catch (error) {
      console.error('批量导入失败:', error);
      // 增强错误日志输出
      console.log('错误状态:', error.status || error.response?.status);
      console.log('错误响应:', error.response?.data);
      
      // 创建一个更友好的错误显示
      let errorTitle = '批量导入失败';
      let errorContent;
      
      if (error.response && error.response.data) {
        const errorData = error.response.data;
        
        // 检查各种可能的错误格式
        if (errorData.detail) {
          const detail = errorData.detail;
          if (typeof detail === 'string') {
            // 简单字符串错误
            errorContent = (
              <div>
                <p>{detail}</p>
              </div>
            );
          } else if (Array.isArray(detail) && detail.length > 0) {
            // 错误数组
            errorContent = (
              <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {detail.map((err, index) => (
                  <div key={index} style={{ marginBottom: '8px' }}>
                    <strong>第 {index + 1} 条记录:</strong> {err.msg || JSON.stringify(err)}
                  </div>
                ))}
              </div>
            );
          } else if (typeof detail === 'object' && detail !== null) {
            // 对象类型错误
            errorContent = (
              <div>
                <pre style={{ whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(detail, null, 2)}
                </pre>
              </div>
            );
          }
        } else if (Array.isArray(errorData.errors) && errorData.errors.length > 0) {
          // errors 数组形式的错误
          errorContent = (
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {errorData.errors.map((err, index) => {
                const errText = typeof err === 'string' ? err : (err.error || err.msg || JSON.stringify(err));
                return (
                  <div key={index} style={{ marginBottom: '8px' }}>
                    <strong>错误 {index + 1}:</strong> {errText}
                  </div>
                );
              })}
            </div>
          );
        } else {
          // 其他情况，显示整个错误对象
          errorContent = (
            <div>
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(errorData, null, 2)}
              </pre>
            </div>
          );
        }
      } else {
        // 没有响应数据的情况
        errorContent = (
          <div>
            <p>{error.message || '网络错误或服务器无响应'}</p>
          </div>
        );
      }
      
      // 使用Modal显示更详细的错误信息
      Modal.error({
        title: errorTitle,
        content: errorContent,
        width: 600
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="批量导入字段权限"
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
              <Text code>数据库名,表名,列名,脱敏类型,用户名1+用户名2+...,角色名1+角色名2+...</Text>
            </Paragraph>
            <Paragraph>
              说明：
              <ul>
                <li>字段之间使用逗号或制表符分隔</li>
                <li>数据库名、表名、列名和脱敏类型为必填项</li>
                <li>脱敏类型必须是以下之一: 手机号, 身份证, 银行卡号, 座机号, 姓名, 原文</li>
                <li>用户名和角色名至少填写一个</li>
                <li>多个用户名或角色名之间使用加号(+)分隔</li>
                <li>示例：<Text code>test_db,users,phone,手机号,admin+guest,</Text> 或 <Text code>test_db,orders,id_card,身份证,user1,manager+viewer</Text></li>
                <li>多用户多角色将一一对应创建权限记录，例如 <Text code>test_db,users,phone,手机号,admin+guest,manager+viewer</Text> 会创建2条记录：admin-manager和guest-viewer</li>
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

export default ColumnPermissionBatchImport;
