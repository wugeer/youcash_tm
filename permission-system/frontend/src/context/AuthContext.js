import React, { createContext, useState, useEffect, useContext } from 'react';
import { message } from 'antd';
import { login as apiLogin, getUserInfo } from '../api/auth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 检查用户是否已登录
  useEffect(() => {
    const checkLoginStatus = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const userInfo = await getUserInfo();
          setCurrentUser(userInfo);
          setIsAuthenticated(true);
        } catch (error) {
          // 如果获取用户信息失败，清除token
          localStorage.removeItem('token');
        } finally {
          setLoading(false);
        }
      } else {
        setLoading(false);
      }
    };

    checkLoginStatus();
  }, []);

  // 用户登录
  const login = async (credentials) => {
    console.log('Sending credentials to backend:', credentials);
    try {
      const response = await apiLogin(credentials);
      const { access_token } = response;
      localStorage.setItem('token', access_token);
      
      // 获取用户信息
      const userInfo = await getUserInfo();
      setCurrentUser(userInfo);
      setIsAuthenticated(true);
      message.success('登录成功');
      
      // 强制刷新页面，确保应用状态完全重新初始化
      // 为路径添加末尾斜杠，避免重定向问题
      setTimeout(() => {
        window.location.href = '/table-permissions/';
      }, 300); // 等待一小段时间以确保消息提示显示
      
      return true;
    } catch (error) {
      return false;
    }
  };

  // 用户登出
  const logout = () => {
    localStorage.removeItem('token');
    setCurrentUser(null);
    setIsAuthenticated(false);
    message.success('已退出登录');
  };

  const value = {
    currentUser,
    loading,
    isAuthenticated,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

export default AuthContext;
