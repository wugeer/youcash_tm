import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import 'antd/dist/reset.css';
import './index.css';
import App from './App';

const theme = {
  token: {
    colorPrimary: '#6D28D9', // A deep purple, inspired by Claude's branding
    fontFamily: "inherit", // Use the same font as the body
    borderRadius: 6,
    
    // Base Colors
    colorText: '#1F2937', // Dark Gray 800
    colorTextSecondary: '#4B5563', // Gray 600
    colorTextTertiary: '#6B7280', // Gray 500
    
    colorBgLayout: '#FFEFD5', // PapayaWhip (for page backgrounds)
    colorBgBase: '#FFEFD5', // Base background
    colorBgElevated: '#FFEFD5', // Elevated surfaces
    colorBgContainer: '#FFEFD5', // PapayaWhip (for cards, modals, etc.)
    colorBorder: '#E5E7EB', // Gray 200
    
    // Status Colors
    colorSuccess: '#059669', // Emerald 600
    colorWarning: '#D97706', // Amber 600
    colorError: '#DC2626', // Red 600
    colorInfo: '#2563EB', // Blue 600
  },
  components: {
    Layout: {
      headerBg: '#FFEFD5',
      siderBg: '#FFEFD5',
      bodyBg: '#FFEFD5',
      headerPadding: '0 24px',
    },
    Menu: {
      itemBg: 'transparent',
      itemColor: '#374151', // Gray 700
      itemHoverBg: '#F3F4F6', // Gray 100
      itemSelectedBg: '#EDE9FE', // Violet 100
      itemSelectedColor: '#5B21B6', // Violet 700
    },
    Button: {
      primaryColor: '#FFFFFF', // Text color for primary button
      defaultBg: '#FFFFFF',
      defaultBorderColor: '#D1D5DB', // Gray 300
    },
    Card: {
      headerBg: 'transparent',
    },
    Table: {
      headerBg: '#F9FAFB', // Gray 50
    }
  },
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <ConfigProvider 
      locale={zhCN}
      theme={theme}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>
);
