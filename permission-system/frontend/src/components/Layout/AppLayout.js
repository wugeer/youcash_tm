import React, { useState } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space } from 'antd';
import { 
  MenuUnfoldOutlined, 
  MenuFoldOutlined,
  UserOutlined,
  TableOutlined,
  ColumnHeightOutlined,
  FilterOutlined,
  LogoutOutlined,
  HddOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const { Header, Sider, Content } = Layout;

const AppLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { currentUser, logout } = useAuth();

  // 导航菜单项
  const menuItems = [
    {
      key: '/table-permissions',
      icon: <TableOutlined />,
      label: '表权限管理',
    },
    {
      key: '/column-permissions',
      icon: <ColumnHeightOutlined />,
      label: '字段权限管理',
    },
    {
      key: '/row-permissions',
      icon: <FilterOutlined />,
      label: '行权限管理',
    },
    {
      key: '/hdfs-quotas',
      icon: <HddOutlined />,
      label: 'HDFS配额管理',
    },
  ];

  // 用户下拉菜单
  const userMenu = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout();
        navigate('/login');
      },
    },
  ];

  // 菜单点击处理
  const handleMenuClick = (e) => {
    navigate(e.key);
  };

  // 获取当前选中的菜单项
  const getSelectedKey = () => {
    const path = location.pathname;
    for (const item of menuItems) {
      if (path.startsWith(item.key)) {
        return [item.key];
      }
    }
    return [];
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed} theme="light">
        <div style={{ height: 32, margin: 16, background: 'rgba(0,0,0,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <h3 style={{ color: '#fff', margin: 0 }}>权限管理系统</h3>
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={getSelectedKey()}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: 0, background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: '16px', width: 64, height: 64 }}
          />
          <div style={{ marginRight: 20 }}>
            <Dropdown menu={{ items: userMenu }} placement="bottomRight">
              <Space>
                <Avatar icon={<UserOutlined />} />
                <span>{currentUser?.username || 'User'}</span>
              </Space>
            </Dropdown>
          </div>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            background: '#fff',
            minHeight: 280,
          }}
        >
          {children}
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
