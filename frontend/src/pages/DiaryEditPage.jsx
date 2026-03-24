/**
 * 日记编辑页 - 创建/编辑日记
 */
import React, { useState, useEffect, useContext } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Form, Input, Select, Button, Switch, Tag, Spin, message } from 'antd'
import { SaveOutlined } from '@ant-design/icons'
import { diaryAPI, scenicAPI } from '../services/api'
import { UserContext } from '../App'

const { TextArea } = Input

function DiaryEditPage() {
  const { id } = useParams()
  const { user } = useContext(UserContext)
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(!!id)
  const [submitting, setSubmitting] = useState(false)
  const [scenicOptions, setScenicOptions] = useState([])
  const [tags, setTags] = useState([])
  const [tagInput, setTagInput] = useState('')
  const navigate = useNavigate()
  const isEdit = !!id

  useEffect(() => {
    if (!user) { message.warning('请先登录'); navigate('/login'); return }

    scenicAPI.list({ per_page: 200 })
      .then(res => setScenicOptions((res.data?.items || []).map(s => ({ value: s.id, label: s.name }))))
      .catch(() => {})

    if (isEdit) {
      diaryAPI.detail(id)
        .then(res => {
          const d = res.data
          form.setFieldsValue({ title: d.title, content: d.content, scenic_id: d.scenic_id, destination: d.destination, is_public: d.is_public })
          setTags(d.tags || [])
        })
        .catch(() => {})
        .finally(() => setLoading(false))
    }
  }, [id])

  const handleSubmit = async (values) => {
    setSubmitting(true)
    try {
      const data = { ...values, tags }
      if (isEdit) {
        await diaryAPI.update(id, data)
        message.success('更新成功')
      } else {
        await diaryAPI.create(data)
        message.success('创建成功')
      }
      navigate('/diary?tab=my')
    } catch (e) { /* ignore */ }
    setSubmitting(false)
  }

  const addTag = () => {
    const t = tagInput.trim()
    if (t && !tags.includes(t)) { setTags([...tags, t]) }
    setTagInput('')
  }

  if (loading) return <Spin size="large" className="flex justify-center py-20" />

  return (
    <div className="max-w-3xl mx-auto">
      <Card title={isEdit ? '编辑日记' : '写旅游日记'}>
        <Form form={form} layout="vertical" onFinish={handleSubmit}
              initialValues={{ is_public: true }}>
          <Form.Item name="title" label="标题" rules={[{ required: true, message: '请输入标题' }]}>
            <Input placeholder="输入日记标题" maxLength={200} />
          </Form.Item>
          <Form.Item name="scenic_id" label="关联景区/校园">
            <Select placeholder="选择关联的景区或校园" options={scenicOptions}
                    showSearch optionFilterProp="label" allowClear
                    onChange={(v) => {
                      const s = scenicOptions.find(o => o.value === v)
                      if (s) form.setFieldValue('destination', s.label)
                    }} />
          </Form.Item>
          <Form.Item name="destination" label="目的地">
            <Input placeholder="旅游目的地名称" />
          </Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true, message: '请输入内容' }]}>
            <TextArea rows={12} placeholder="记录你的旅行故事..." showCount maxLength={10000} />
          </Form.Item>
          <Form.Item label="标签">
            <div className="flex flex-wrap gap-1 mb-2">
              {tags.map((t, i) => (
                <Tag key={i} closable onClose={() => setTags(tags.filter((_, idx) => idx !== i))}>{t}</Tag>
              ))}
            </div>
            <Input.Search
              placeholder="输入标签后回车"
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onSearch={addTag}
              enterButton="添加"
              style={{ maxWidth: 300 }}
            />
          </Form.Item>
          <Form.Item name="is_public" label="是否公开" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={submitting} icon={<SaveOutlined />} size="large">
              {isEdit ? '保存修改' : '发布日记'}
            </Button>
            <Button className="ml-3" onClick={() => navigate(-1)}>取消</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}

export default DiaryEditPage
