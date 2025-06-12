import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import TablePermissionList from '../pages/tablePermission/TablePermissionList';
import { AuthProvider } from '../context/AuthContext';
import * as tablePermissionAPI from '../api/tablePermission';

// 模拟API调用
jest.mock('../api/tablePermission');

// 模拟数据
const mockPermissions = {
  items: [
    {
      id: 1,
      db_name: 'testdb',
      table_name: 'users',
      user_name: 'admin',
      role_name: 'analyst',
      create_time: '2025-06-12T10:30:00'
    },
    {
      id: 2,
      db_name: 'testdb',
      table_name: 'orders',
      user_name: 'admin',
      role_name: 'analyst',
      create_time: '2025-06-12T11:30:00'
    }
  ],
  total: 2
};

describe('TablePermissionList Component', () => {
  beforeEach(() => {
    // 模拟API返回
    tablePermissionAPI.getTablePermissions.mockResolvedValue(mockPermissions);
    tablePermissionAPI.deleteTablePermission.mockResolvedValue({});
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  const renderTablePermissionList = () => {
    return render(
      <Router>
        <AuthProvider>
          <TablePermissionList />
        </AuthProvider>
      </Router>
    );
  };

  test('渲染表权限列表', async () => {
    renderTablePermissionList();
    
    // 等待API加载完成
    await waitFor(() => {
      expect(tablePermissionAPI.getTablePermissions).toHaveBeenCalled();
    });
    
    // 验证表格内容显示
    expect(screen.getByText('testdb')).toBeInTheDocument();
    expect(screen.getByText('users')).toBeInTheDocument();
    expect(screen.getByText('orders')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByText('analyst')).toBeInTheDocument();
  });

  test('搜索功能', async () => {
    renderTablePermissionList();
    
    // 等待API加载完成
    await waitFor(() => {
      expect(tablePermissionAPI.getTablePermissions).toHaveBeenCalled();
    });
    
    // 填写搜索表单
    const dbNameInput = screen.getByLabelText(/数据库名/i);
    fireEvent.change(dbNameInput, { target: { value: 'searchdb' } });
    
    // 点击搜索按钮
    const searchButton = screen.getByRole('button', { name: /搜索/i });
    fireEvent.click(searchButton);
    
    // 验证搜索请求
    await waitFor(() => {
      expect(tablePermissionAPI.getTablePermissions).toHaveBeenCalledWith(
        expect.objectContaining({
          db_name: 'searchdb'
        })
      );
    });
  });

  test('删除表权限', async () => {
    renderTablePermissionList();
    
    // 等待API加载完成
    await waitFor(() => {
      expect(tablePermissionAPI.getTablePermissions).toHaveBeenCalled();
    });
    
    // 找到删除按钮并点击
    const deleteButtons = screen.getAllByRole('button', { name: /删除/i });
    fireEvent.click(deleteButtons[0]);
    
    // 确认删除
    const confirmButton = screen.getByRole('button', { name: /确定/i });
    fireEvent.click(confirmButton);
    
    // 验证删除请求和列表刷新
    await waitFor(() => {
      expect(tablePermissionAPI.deleteTablePermission).toHaveBeenCalledWith(1);
      expect(tablePermissionAPI.getTablePermissions).toHaveBeenCalledTimes(2);
    });
  });

  test('添加新权限按钮', async () => {
    renderTablePermissionList();
    
    // 等待API加载完成
    await waitFor(() => {
      expect(tablePermissionAPI.getTablePermissions).toHaveBeenCalled();
    });
    
    // 点击添加按钮
    const addButton = screen.getByRole('button', { name: /添加表权限/i });
    fireEvent.click(addButton);
    
    // 验证表单模态框打开
    await waitFor(() => {
      expect(screen.getByText(/添加表权限/i)).toBeInTheDocument();
    });
  });
});
