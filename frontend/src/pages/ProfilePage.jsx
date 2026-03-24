/**
 * 个人中心页
 */
import React, { useContext, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Form, Input, Select, Button, Tag, message, Descriptions, Divider } from 'antd'
import { UserOutlined, SaveOutlined } from '@ant-design/icons'
import { authAPI } from '../services/api'
import { UserContext } from '../App'

const interestOptions = [
  '自然风光', '历史文化', '美食', '主题乐园', '科技', '博物馆',
  '摄影', '建筑', '户外运动', '文艺', '购物', '咖啡', '海滨', '古镇',
]

function ProfilePage() {
  const { user, setUser } = useContext(UserContext)
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()
  const navigate = useNavigate()

  if (!user) {
    navigate('/login')
    return null
  }

  const handleSave = async (values) => {
    setLoading(true)
    try {
      const res = await authAPI.updateProfile(values)
      setUser(res.data)
      message.success('更新成功')
      setEditing(false)
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card title="个人中心">
        {!editing ? (
          <>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="用户名">{user.username}</Descriptions.Item>
              <Descriptions.Item label="昵称">{user.nickname}</Descriptions.Item>
              <Descriptions.Item label="邮箱">{user.email}</Descriptions.Item>
              <Descriptions.Item label="兴趣标签">
                {user.interests?.map((t, i) => <Tag key={i} color="blue">{t}</Tag>)}
                {(!user.interests || user.interests.length === 0) && <span className="text-gray-400">未设置</span>}
              </Descriptions.Item>
              <Descriptions.Item label="注册时间">{user.created_at?.substring(0, 10)}</Descriptions.Item>
            </Descriptions>
            <div className="mt-4">
              <Button type="primary" onClick={() => {
                form.setFieldsValue({ nickname: user.nickname, email: user.email, interests: user.interests || [] })
                setEditing(true)
              }}>编辑资料</Button>
            </div>
          </>
        ) : (
          <Form form={form} layout="vertical" onFinish={handleSave}>
            <Form.Item name="nickname" label="昵称">
              <Input placeholder="设置昵称" />
            </Form.Item>
            <Form.Item name="email" label="邮箱" rules={[{ type: 'email', message: '请输入有效邮箱' }]}>
              <Input placeholder="邮箱" />
            </Form.Item>
            <Form.Item name="interests" label="兴趣标签">
              <Select mode="multiple" placeholder="选择兴趣标签"
                      options={interestOptions.map(i => ({ value: i, label: i }))} />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} icon={<SaveOutlined />}>保存</Button>
              <Button className="ml-3" onClick={() => setEditing(false)}>取消</Button>
            </Form.Item>
          </Form>
        )}
      </Card>
    </div>
  )
}

export default ProfilePage
