import React, { useState } from 'react';
import { Modal, Form, Input, Button, message, Alert, Typography } from 'antd';
import { batchImportHdfsQuotas } from '../../api/hdfsQuota';

const { TextArea } = Input;
const { Paragraph, Text } = Typography;

const HdfsQuotaBatchImport = ({ visible, onCancel, onSuccess }) => {
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
      
      // 检查每行至少有2个字段
      if (parts.length < 2) {
        errors.push(`第 ${index + 1} 行: 格式不正确，需要数据库名和HDFS配额`);
        return;
      }

      // 解析字段
      const [db_name, hdfs_quota] = parts;
      
      // 验证必填字段
      if (!db_name) {
        errors.push(`第 ${index + 1} 行: 数据库名不能为空`);
        return;
      }
      
      // 验证配额是否为有效数字且大于0
      const quota = parseFloat(hdfs_quota);
      if (isNaN(quota) || quota <= 0) {
        errors.push(`第 ${index + 1} 行: HDFS配额必须是大于0的数值`);
        return;
      }

      // 添加到解析后的数据中
      parsedData.push({
        db_name,
        hdfs_quota: quota
      });
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
      const result = await batchImportHdfsQuotas(parseResult.data);
      message.success(`成功导入 ${result.success} 条HDFS配额记录，失败 ${result.failed} 条`);
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
      title="批量导入HDFS配额"
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
              <Text code>数据库名,HDFS配额(GB)</Text>
            </Paragraph>
            <Paragraph>
              说明：
              <ul>
                <li>字段之间使用逗号或制表符分隔</li>
                <li>数据库名和HDFS配额均为必填项</li>
                <li>HDFS配额必须是大于0的数值，单位为GB</li>
                <li>示例：<Text code>test_db,100</Text> 或 <Text code>hive_db,200.5</Text></li>
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

export default HdfsQuotaBatchImport;
