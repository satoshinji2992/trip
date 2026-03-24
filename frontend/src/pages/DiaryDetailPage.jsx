/**
 * 日记详情页 - 查看日记、评论、评分
 */
import React, { useState, useEffect, useContext } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Tag, Rate, Button, Divider, Input, List, Avatar, Spin, Empty, Space, message, Statistic, Row, Col } from 'antd'
import { UserOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MessageOutlined, CompressOutlined } from '@ant-design/icons'
import { diaryAPI } from '../services/api'
import { UserContext } from '../App'

const { TextArea } = Input

function DiaryDetailPage() {
  const { id } = useParams()
  const { user } = useContext(UserContext)
  const [diary, setDiary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [commentContent, setCommentContent] = useState('')
  const [commentRating, setCommentRating] = useState(5)
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  const fetchDiary = () => {
    diaryAPI.detail(id)
      .then((res) => setDiary(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchDiary() }, [id])

  const handleComment = async () => {
    if (!user) { message.warning('请先登录'); return }
    if (!commentContent.trim()) { message.warning('请输入评论内容'); return }
    setSubmitting(true)
    try {
      await diaryAPI.comment(id, { content: commentContent, rating: commentRating })
      message.success('评论成功')
      setCommentContent('')
      setCommentRating(5)
      fetchDiary()
    } catch (e) { /* ignore */ }
    setSubmitting(false)
  }

  const handleDelete = async () => {
    try {
      await diaryAPI.delete(id)
      message.success('删除成功')
      navigate('/diary')
    } catch (e) { /* ignore */ }
  }

  if (loading) return <Spin size="large" className="flex justify-center py-20" />
  if (!diary) return <Empty description="日记不存在" />

  const isOwner = user && user.id === diary.user_id

  return (
    <div className="max-w-4xl mx-auto">
      <Card>
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold mb-2">{diary.title}</h1>
            <Space className="text-gray-500 text-sm">
              <span><UserOutlined /> {diary.author_name}</span>
              {diary.destination && <Tag color="blue">{diary.destination}</Tag>}
              <span>{diary.created_at?.substring(0, 10)}</span>
            </Space>
          </div>
          {isOwner && (
            <Space>
              <Button icon={<EditOutlined />} onClick={() => navigate(`/diary/edit/${id}`)}>编辑</Button>
              <Button danger icon={<DeleteOutlined />} onClick={handleDelete}>删除</Button>
            </Space>
          )}
        </div>

        <Row gutter={16} className="mb-4">
          <Col span={6}>
            <Statistic title="浏览量" value={diary.view_count} prefix={<EyeOutlined />} />
          </Col>
          <Col span={6}>
            <Statistic title="评分" value={diary.average_rating} prefix={<Rate disabled value={1} count={1} style={{ fontSize: 14 }} />} precision={1} />
          </Col>
          <Col span={6}>
            <Statistic title="评论数" value={diary.comment_count} prefix={<MessageOutlined />} />
          </Col>
          <Col span={6}>
            {diary.compression_ratio && (
              <Statistic title="压缩率" value={diary.compression_ratio * 100} suffix="%" prefix={<CompressOutlined />} precision={1} />
            )}
          </Col>
        </Row>

        {diary.tags && diary.tags.length > 0 && (
          <div className="mb-4">
            {diary.tags.map((t, i) => <Tag key={i} color="processing">{t}</Tag>)}
          </div>
        )}

        <Divider />

        <div className="prose max-w-none mb-6" style={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
          {diary.content}
        </div>

        {diary.images && diary.images.length > 0 && (
          <>
            <Divider>图片</Divider>
            <div className="grid grid-cols-3 gap-4 mb-6">
              {diary.images.map((img) => (
                <div key={img.id} className="aspect-video bg-gray-100 rounded overflow-hidden">
                  <img src={img.image_path} alt={img.description} className="w-full h-full object-cover" />
                </div>
              ))}
            </div>
          </>
        )}

        <Divider>评论 ({diary.comments?.length || 0})</Divider>

        {user && (
          <Card size="small" className="mb-4 bg-gray-50">
            <div className="mb-2">
              <span className="mr-2">评分:</span>
              <Rate value={commentRating} onChange={setCommentRating} />
            </div>
            <TextArea
              rows={3}
              placeholder="写下你的评论..."
              value={commentContent}
              onChange={(e) => setCommentContent(e.target.value)}
            />
            <div className="text-right mt-2">
              <Button type="primary" loading={submitting} onClick={handleComment}>发表评论</Button>
            </div>
          </Card>
        )}

        <List
          dataSource={diary.comments || []}
          locale={{ emptyText: '暂无评论' }}
          renderItem={(c) => (
            <List.Item>
              <List.Item.Meta
                avatar={<Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />}
                title={
                  <Space>
                    <span>{c.user_name}</span>
                    <Rate disabled value={c.rating} allowHalf style={{ fontSize: 12 }} />
                    <span className="text-xs text-gray-400">{c.created_at?.substring(0, 10)}</span>
                  </Space>
                }
                description={c.content}
              />
            </List.Item>
          )}
        />
      </Card>
    </div>
  )
}

export default DiaryDetailPage
