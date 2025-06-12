import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import AppLayout from './components/Layout/AppLayout';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import TablePermissionList from './pages/tablePermission/TablePermissionList';
import ColumnPermissionList from './pages/columnPermission/ColumnPermissionList';
import RowPermissionList from './pages/rowPermission/RowPermissionList';

// 受保护的路由组件
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div>正在加载...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return (
    <AppLayout>
      {children}
    </AppLayout>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* 公共路由 */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* 受保护的路由 */}
          <Route 
            path="/table-permissions" 
            element={
              <ProtectedRoute>
                <TablePermissionList />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/column-permissions" 
            element={
              <ProtectedRoute>
                <ColumnPermissionList />
              </ProtectedRoute>
            } 
          />
          
          <Route 
            path="/row-permissions" 
            element={
              <ProtectedRoute>
                <RowPermissionList />
              </ProtectedRoute>
            } 
          />
          
          {/* 重定向 */}
          <Route path="/" element={<Navigate to="/table-permissions" replace />} />
          <Route path="*" element={<Navigate to="/table-permissions" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
};

export default App;
