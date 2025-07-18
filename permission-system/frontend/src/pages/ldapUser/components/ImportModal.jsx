import React, { useState } from 'react';
import { Modal, Button, Upload, message, Alert, Typography } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const { Text } = Typography;

/**
 * LDAP用户批量导入模态框组件
 * 
 * @param {Object} props - 组件属性
 * @param {boolean} props.visible - 模态框是否可见
 * @param {Function} props.onClose - 关闭模态框的回调函数
 * @param {Function} props.onImport - 导入文件的回调函数
 */
const ImportModal = ({ visible, onClose, onImport }) => {
  const [fileList, setFileList] = useState([]);
  const [fileContent, setFileContent] = useState('');
  const [loading, setLoading] = useState(false);

  // CSV模板内容
  const csvTemplate = 'username,password,role_name,department_name,hdfs_quota,description\n' +
                      'user1,password123,analyst,finance,100,财务部分析师\n' +
                      'user2,password456,developer,it,200,IT部开发人员';

  // 重置状态
  const resetState = () => {
    setFileList([]);
    setFileContent('');
  };

  // 关闭模态框
  const handleClose = () => {
    resetState();
    onClose();
  };

  // 处理文件上传
  const handleUpload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target.result;
        setFileContent(content);
      } catch (error) {
        message.error('文件读取失败: ' + error.message);
      }
    };
    reader.onerror = () => {
      message.error('文件读取失败');
    };
    reader.readAsText(file);
    
    // 更新文件列表
    setFileList([file]);
    return false; // 阻止自动上传
  };

  // 提交导入
  const handleSubmit = async () => {
    if (!fileContent) {
      message.error('请先选择CSV文件');
      return;
    }

    setLoading(true);
    try {
      await onImport(fileContent);
      resetState();
    } catch (error) {
      message.error('导入失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 下载模板
  const handleDownloadTemplate = () => {
    const blob = new Blob([csvTemplate], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'ldap_users_template.csv';
    link.click();
  };

  return (
    <Modal
      title="批量导入LDAP用户"
      visible={visible}
      onCancel={handleClose}
      footer={[
        <Button key="download" onClick={handleDownloadTemplate}>
          下载模板
        </Button>,
        <Button key="cancel" onClick={handleClose}>
          取消
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={loading}
          onClick={handleSubmit}
          disabled={!fileContent}
        >
          导入
        </Button>,
      ]}
      destroyOnClose
    >
      <Alert
        message="导入说明"
        description={
          <div>
            <p>1. 请使用CSV格式文件，包含以下字段：username, password, role_name, department_name, hdfs_quota, description</p>
            <p>2. 文件第一行必须是字段名</p>
            <p>3. username, password, role_name, department_name 为必填字段</p>
            <p>4. hdfs_quota 默认为 100 GB</p>
            <p>5. 点击"下载模板"获取标准格式</p>
          </div>
        }
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Upload.Dragger
        accept=".csv"
        beforeUpload={handleUpload}
        fileList={fileList}
        onRemove={() => {
          setFileList([]);
          setFileContent('');
        }}
        maxCount={1}
      >
        <p className="ant-upload-drag-icon">
          <UploadOutlined />
        </p>
        <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p className="ant-upload-hint">支持 .csv 格式的文件</p>
      </Upload.Dragger>

      {fileContent && (
        <div style={{ marginTop: 16 }}>
          <Text strong>已选择文件：</Text>
          <Text>{fileList[0]?.name}</Text>
        </div>
      )}
    </Modal>
  );
};

export default ImportModal;
