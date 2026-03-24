/**
 * 登录页
 */
import React, { useContext, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Card, Form, Input, Button, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { authAPI } from '../services/api'
import { UserContext } from '../App'

function LoginPage() {
  const { setUser } = useContext(UserContext)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (values) => {
    setLoading(true)
    try {
      const res = await authAPI.login(values)
      setUser(res.data)
      message.success('登录成功')
      navigate('/')
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  return (
    <div className="flex justify-center items-center py-20">
      <Card title="用户登录" className="w-full max-w-md">
        <Form onFinish={handleSubmit} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>登录</Button>
          </Form.Item>
          <div className="text-center">
            没有账号？<Link to="/register">立即注册</Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default LoginPage
