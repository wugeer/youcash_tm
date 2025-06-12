import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter as Router } from 'react-router-dom';
import Login from '../pages/auth/Login';
import { AuthProvider } from '../context/AuthContext';

// 模拟react-router-dom的useNavigate功能
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
}));

// 模拟auth上下文
jest.mock('../context/AuthContext', () => {
  const originalModule = jest.requireActual('../context/AuthContext');
  return {
    ...originalModule,
    useAuth: () => ({
      login: jest.fn().mockImplementation((username, password) => {
        if (username === 'testuser' && password === 'password123') {
          return Promise.resolve(true);
        } else {
          return Promise.resolve(false);
        }
      }),
    }),
  };
});

describe('Login Component', () => {
  const renderLoginComponent = () => {
    return render(
      <Router>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </Router>
    );
  };

  test('渲染登录表单', () => {
    renderLoginComponent();
    expect(screen.getByPlaceholderText(/用户名/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/密码/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument();
  });

  test('表单验证 - 提交空表单', async () => {
    renderLoginComponent();
    const submitButton = screen.getByRole('button', { name: /登录/i });
    
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/请输入用户名/i)).toBeInTheDocument();
    });
  });

  test('表单提交 - 成功登录', async () => {
    renderLoginComponent();
    const usernameInput = screen.getByPlaceholderText(/用户名/i);
    const passwordInput = screen.getByPlaceholderText(/密码/i);
    const submitButton = screen.getByRole('button', { name: /登录/i });
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(submitButton).toHaveAttribute('disabled');
    });
  });

  test('表单提交 - 用户名密码错误', async () => {
    renderLoginComponent();
    const usernameInput = screen.getByPlaceholderText(/用户名/i);
    const passwordInput = screen.getByPlaceholderText(/密码/i);
    const submitButton = screen.getByRole('button', { name: /登录/i });
    
    fireEvent.change(usernameInput, { target: { value: 'wronguser' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpass' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(submitButton).not.toHaveAttribute('disabled');
    });
  });
});
