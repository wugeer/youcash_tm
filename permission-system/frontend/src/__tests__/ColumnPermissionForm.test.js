import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ColumnPermissionForm from '../pages/columnPermission/ColumnPermissionForm';
import * as columnPermissionAPI from '../api/columnPermission';

// 模拟API调用
jest.mock('../api/columnPermission');

describe('ColumnPermissionForm Component', () => {
  const mockOnCancel = jest.fn();
  const mockOnSuccess = jest.fn();
  
  const mockInitialValues = {
    id: 1,
    db_name: 'testdb',
    table_name: 'users',
    col_name: 'phone',
    mask_type: '手机号',
    user_name: 'admin',
    role_name: 'analyst'
  };

  beforeEach(() => {
    columnPermissionAPI.createColumnPermission.mockResolvedValue({ id: 999, ...mockInitialValues });
    columnPermissionAPI.updateColumnPermission.mockResolvedValue({ ...mockInitialValues, mask_type: '身份证' });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('渲染创建字段权限表单', () => {
    render(
      <ColumnPermissionForm 
        visible={true}
        onCancel={mockOnCancel}
        onSuccess={mockOnSuccess}
      />
    );
    
    expect(screen.getByText('添加字段权限')).toBeInTheDocument();
    expect(screen.getByLabelText('数据库名')).toBeInTheDocument();
    expect(screen.getByLabelText('表名')).toBeInTheDocument();
    expect(screen.getByLabelText('字段名')).toBeInTheDocument();
    expect(screen.getByLabelText('脱敏类型')).toBeInTheDocument();
    expect(screen.getByLabelText('用户名')).toBeInTheDocument();
    expect(screen.getByLabelText('角色名')).toBeInTheDocument();
  });

  test('渲染编辑字段权限表单', () => {
    render(
      <ColumnPermissionForm 
        visible={true}
        onCancel={mockOnCancel}
        onSuccess={mockOnSuccess}
        initialValues={mockInitialValues}
      />
    );
    
    expect(screen.getByText('编辑字段权限')).toBeInTheDocument();
    expect(screen.getByDisplayValue('testdb')).toBeInTheDocument();
    expect(screen.getByDisplayValue('users')).toBeInTheDocument();
    expect(screen.getByDisplayValue('phone')).toBeInTheDocument();
    expect(screen.getByDisplayValue('admin')).toBeInTheDocument();
    expect(screen.getByDisplayValue('analyst')).toBeInTheDocument();
  });

  test('创建新字段权限', async () => {
    render(
      <ColumnPermissionForm 
        visible={true}
        onCancel={mockOnCancel}
        onSuccess={mockOnSuccess}
      />
    );
    
    // 填写表单
    fireEvent.change(screen.getByLabelText('数据库名'), { target: { value: 'newdb' } });
    fireEvent.change(screen.getByLabelText('表名'), { target: { value: 'customers' } });
    fireEvent.change(screen.getByLabelText('字段名'), { target: { value: 'id_card' } });
    fireEvent.click(screen.getByLabelText('脱敏类型'));
    fireEvent.click(screen.getByText('身份证'));
    fireEvent.change(screen.getByLabelText('用户名'), { target: { value: 'tester' } });
    fireEvent.change(screen.getByLabelText('角色名'), { target: { value: 'viewer' } });
    
    // 提交表单
    const submitButton = screen.getByRole('button', { name: '保存' });
    fireEvent.click(submitButton);
    
    // 验证API调用
    await waitFor(() => {
      expect(columnPermissionAPI.createColumnPermission).toHaveBeenCalledWith({
        db_name: 'newdb',
        table_name: 'customers',
        col_name: 'id_card',
        mask_type: '身份证',
        user_name: 'tester',
        role_name: 'viewer'
      });
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  test('更新字段权限', async () => {
    render(
      <ColumnPermissionForm 
        visible={true}
        onCancel={mockOnCancel}
        onSuccess={mockOnSuccess}
        initialValues={mockInitialValues}
      />
    );
    
    // 修改表单
    fireEvent.click(screen.getByLabelText('脱敏类型'));
    fireEvent.click(screen.getByText('身份证'));
    
    // 提交表单
    const submitButton = screen.getByRole('button', { name: '保存' });
    fireEvent.click(submitButton);
    
    // 验证API调用
    await waitFor(() => {
      expect(columnPermissionAPI.updateColumnPermission).toHaveBeenCalledWith(
        1, 
        expect.objectContaining({
          mask_type: '身份证'
        })
      );
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  test('取消表单', () => {
    render(
      <ColumnPermissionForm 
        visible={true}
        onCancel={mockOnCancel}
        onSuccess={mockOnSuccess}
      />
    );
    
    const cancelButton = screen.getByRole('button', { name: '取消' });
    fireEvent.click(cancelButton);
    
    expect(mockOnCancel).toHaveBeenCalled();
  });
});
