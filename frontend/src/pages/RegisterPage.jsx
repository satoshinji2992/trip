/**
 * 注册页
 */
import React, { useContext, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Card, Form, Input, Button, Select, Tag, message } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { authAPI } from '../services/api'
import { UserContext } from '../App'

const interestOptions = [
  '自然风光', '历史文化', '美食', '主题乐园', '科技', '博物馆',
  '摄影', '建筑', '户外运动', '文艺', '购物', '咖啡', '海滨', '古镇',
]

function RegisterPage() {
  const { setUser } = useContext(UserContext)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (values) => {
    setLoading(true)
    try {
      const res = await authAPI.register(values)
      setUser(res.data)
      message.success('注册成功')
      navigate('/')
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  return (
    <div className="flex justify-center items-center py-12">
      <Card title="用户注册" className="w-full max-w-md">
        <Form onFinish={handleSubmit} size="large">
          <Form.Item name="username" rules={[{ required: true, message: '请输入用户名' }, { min: 3, message: '用户名至少3个字符' }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名（至少3个字符）" />
          </Form.Item>
          <Form.Item name="email" rules={[{ required: true, message: '请输入邮箱' }, { type: 'email', message: '请输入有效邮箱' }]}>
            <Input prefix={<MailOutlined />} placeholder="邮箱" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: '请输入密码' }, { min: 6, message: '密码至少6个字符' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码（至少6个字符）" />
          </Form.Item>
          <Form.Item name="nickname">
            <Input placeholder="昵称（可选）" />
          </Form.Item>
          <Form.Item name="interests" label="兴趣标签">
            <Select mode="multiple" placeholder="选择你感兴趣的旅游类型" options={interestOptions.map(i => ({ value: i, label: i }))} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>注册</Button>
          </Form.Item>
          <div className="text-center">
            已有账号？<Link to="/login">立即登录</Link>
          </div>
        </Form>
      </Card>
    </div>
  )
}

export default RegisterPage
