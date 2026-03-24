/**
 * 应用根组件 - 路由配置和布局
 */
import React, { useState, useEffect, createContext } from 'react'
import { Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, Button, Space, message } from 'antd'
import {
  HomeOutlined, CompassOutlined, SearchOutlined, BookOutlined,
  CoffeeOutlined, UserOutlined, LoginOutlined, LogoutOutlined,
  EditOutlined, EnvironmentOutlined,
} from '@ant-design/icons'
import { authAPI } from './services/api'

import HomePage from './pages/HomePage'
import ScenicListPage from './pages/ScenicListPage'
import ScenicDetailPage from './pages/ScenicDetailPage'
import RouteplanPage from './pages/RoutePlanPage'
import FacilityPage from './pages/FacilityPage'
import DiaryListPage from './pages/DiaryListPage'
import DiaryDetailPage from './pages/DiaryDetailPage'
import DiaryEditPage from './pages/DiaryEditPage'
import FoodPage from './pages/FoodPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ProfilePage from './pages/ProfilePage'
import IndoorNavPage from './pages/IndoorNavPage'

const { Header, Content, Footer } = Layout

export const UserContext = createContext(null)

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    authAPI.check()
      .then((res) => { if (res.data) setUser(res.data) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleLogout = async () => {
    try {
      await authAPI.logout()
      setUser(null)
      message.success('已登出')
      navigate('/')
    } catch (e) { /* ignore */ }
  }

  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    { key: '/scenic', icon: <CompassOutlined />, label: '旅游推荐' },
    { key: '/diary', icon: <BookOutlined />, label: '旅游日记' },
    { key: '/food', icon: <CoffeeOutlined />, label: '美食推荐' },
  ]

  const userMenuItems = user ? [
    { key: 'profile', icon: <UserOutlined />, label: '个人中心' },
    { key: 'my-diary', icon: <EditOutlined />, label: '我的日记' },
    { type: 'divider' },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
  ] : []

  const handleUserMenu = ({ key }) => {
    if (key === 'profile') navigate('/profile')
    else if (key === 'my-diary') navigate('/diary?tab=my')
    else if (key === 'logout') handleLogout()
  }

  const currentKey = '/' + (location.pathname.split('/')[1] || '')

  return (
    <UserContext.Provider value={{ user, setUser, loading }}>
      <Layout className="min-h-screen">
        <Header className="flex items-center justify-between px-6" style={{ background: '#001529' }}>
          <div className="flex items-center">
            <div className="text-white text-xl font-bold mr-8 cursor-pointer" onClick={() => navigate('/')}>
              <EnvironmentOutlined className="mr-2" />
              个性化旅游系统
            </div>
            <Menu
              theme="dark"
              mode="horizontal"
              selectedKeys={[currentKey]}
              items={menuItems}
              onClick={({ key }) => navigate(key)}
              style={{ flex: 1, minWidth: 400, background: 'transparent', borderBottom: 'none' }}
            />
          </div>
          <div>
            {user ? (
              <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenu }} placement="bottomRight">
                <Space className="cursor-pointer text-white">
                  <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
                  <span>{user.nickname || user.username}</span>
                </Space>
              </Dropdown>
            ) : (
              <Space>
                <Button type="primary" ghost icon={<LoginOutlined />} onClick={() => navigate('/login')}>登录</Button>
                <Button ghost icon={<UserOutlined />} onClick={() => navigate('/register')}>注册</Button>
              </Space>
            )}
          </div>
        </Header>
        <Content className="p-6" style={{ minHeight: 'calc(100vh - 134px)' }}>
          <div className="max-w-7xl mx-auto">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/scenic" element={<ScenicListPage />} />
              <Route path="/scenic/:id" element={<ScenicDetailPage />} />
              <Route path="/route/:scenicId" element={<RouteplanPage />} />
              <Route path="/facility/:scenicId" element={<FacilityPage />} />
              <Route path="/indoor/:buildingId" element={<IndoorNavPage />} />
              <Route path="/diary" element={<DiaryListPage />} />
              <Route path="/diary/:id" element={<DiaryDetailPage />} />
              <Route path="/diary/edit/:id?" element={<DiaryEditPage />} />
              <Route path="/food" element={<FoodPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </Content>
        <Footer className="text-center text-gray-500">
          个性化旅游系统 ©2024 - 课程设计项目
        </Footer>
      </Layout>
    </UserContext.Provider>
  )
}

export default App
