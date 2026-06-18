/**
 * 日记编辑页 - 创建/编辑日记
 */
import React, { useState, useEffect, useContext, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Form, Image, Input, Select, Button, Switch, Tag, Spin, message } from 'antd'
import { DeleteOutlined, InboxOutlined, SaveOutlined } from '@ant-design/icons'
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
  const [images, setImages] = useState([])
  const [pendingImages, setPendingImages] = useState([])
  const [imageDescription, setImageDescription] = useState('')
  const fileInputRef = useRef(null)
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
          setImages(d.images || [])
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
        navigate('/diary?tab=my')
      } else {
        const res = await diaryAPI.create(data)
        if (pendingImages.length > 0) {
          await uploadFiles(res.data.id, pendingImages)
          message.success('创建成功，图片已上传')
        } else {
          message.success('创建成功')
        }
        setPendingImages([])
        navigate(`/diary/edit/${res.data.id}`)
      }
    } catch (e) { /* ignore */ }
    setSubmitting(false)
  }

  const uploadOneFile = async (diaryId, file) => {
    const formData = new FormData()
    formData.append('image', file)
    formData.append('description', imageDescription)
    const res = await diaryAPI.uploadImage(diaryId, formData)
    setImages((prev) => [...prev, res.data])
    return res.data
  }

  const uploadFiles = async (diaryId, files) => {
    for (const file of files) {
      await uploadOneFile(diaryId, file)
    }
    setImageDescription('')
  }

  const handleSelectedFiles = async (selectedFiles) => {
    const files = Array.from(selectedFiles || [])
    if (files.length === 0) return
    if (!isEdit) {
      setPendingImages((prev) => [...prev, ...files])
      message.success(`已选择 ${files.length} 张图片，发布日记后自动上传`)
      return
    }
    try {
      await uploadFiles(id, files)
      message.success(`已上传 ${files.length} 张图片`)
    } catch (e) {
      message.error('图片上传失败')
    }
  }

  const handleNativeFileChange = async (event) => {
    await handleSelectedFiles(event.target.files)
    event.target.value = ''
  }

  const handleImageDrop = async (event) => {
    event.preventDefault()
    await handleSelectedFiles(event.dataTransfer.files)
  }

  const handleDeleteImage = async (imageId) => {
    try {
      await diaryAPI.deleteImage(id, imageId)
      setImages((prev) => prev.filter((img) => img.id !== imageId))
      message.success('图片已删除')
    } catch (e) { /* ignore */ }
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
          <Form.Item label="图片">
            {images.length > 0 && (
              <div className="grid grid-cols-3 gap-3 mb-3">
                {images.map((img) => (
                  <div key={img.id} className="relative aspect-video bg-gray-100 rounded overflow-hidden group">
                    <Image src={img.image_path} alt={img.description || '日记图片'} className="w-full h-full object-cover" />
                    <Button
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      className="absolute top-2 right-2 opacity-90"
                      onClick={() => handleDeleteImage(img.id)}
                    />
                  </div>
                ))}
              </div>
            )}
            <Input
              className="mb-2"
              placeholder="图片说明，可选"
              value={imageDescription}
              onChange={(e) => setImageDescription(e.target.value)}
            />
            <div
              role="button"
              tabIndex={0}
              className="border border-dashed border-gray-300 rounded bg-gray-50 text-center py-8 cursor-pointer hover:border-blue-400 hover:bg-blue-50"
              onClick={() => fileInputRef.current?.click()}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click()
              }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleImageDrop}
            >
              <InboxOutlined className="text-3xl text-blue-500 mb-2" />
              <div className="text-base">
                {pendingImages.length > 0 ? `已选择 ${pendingImages.length} 张图片` : '点击或拖拽图片上传'}
              </div>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={handleNativeFileChange}
            />
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
