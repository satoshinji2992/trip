/**
 * 旅游日记列表页 - 浏览、搜索、推荐排序
 */
import React, { useState, useEffect, useContext } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, Row, Col, Input, Select, Tabs, Tag, Rate, Pagination, Spin, Empty, Button, Space, message } from 'antd'
import { SearchOutlined, PlusOutlined, FireOutlined, BookOutlined, FileSearchOutlined } from '@ant-design/icons'
import { diaryAPI } from '../services/api'
import { UserContext } from '../App'

const { Search } = Input

function DiaryListPage() {
  const { user } = useContext(UserContext)
  const [diaries, setDiaries] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('mixed')
  const [searchQuery, setSearchQuery] = useState('')
  const [searchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState(searchParams.get('tab') || 'public')
  const [searchMode, setSearchMode] = useState('normal')
  const navigate = useNavigate()

  const destination = searchParams.get('destination') || ''

  const fetchPublic = async () => {
    setLoading(true)
    try {
      const res = await diaryAPI.public({ page, per_page: 12, sort_by: sortBy })
      setDiaries(res.data?.items || [])
      setTotal(res.data?.total || 0)
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  const fetchMy = async () => {
    setLoading(true)
    try {
      const res = await diaryAPI.my({ page, per_page: 12 })
      setDiaries(res.data?.items || [])
      setTotal(res.data?.total || 0)
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  const fetchByDestination = async () => {
    if (!destination) return
    setLoading(true)
    try {
      const res = await diaryAPI.byDestination({ destination, sort_by: sortBy })
      setDiaries(res.data?.items || [])
      setTotal(res.data?.total || 0)
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => {
    if (destination) { fetchByDestination(); return }
    if (activeTab === 'my' && user) fetchMy()
    else fetchPublic()
  }, [page, sortBy, activeTab, destination])

  const handleSearch = async () => {
    if (!searchQuery.trim()) { message.warning('请输入搜索关键词'); return }
    setLoading(true)
    try {
      let res
      if (searchMode === 'fulltext') {
        res = await diaryAPI.fulltextSearch({ q: searchQuery, limit: 50 })
      } else {
        res = await diaryAPI.search({ q: searchQuery, sort_by: sortBy })
      }
      setDiaries(res.data?.items || [])
      setTotal(res.data?.total || 0)
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  const DiaryCard = ({ diary }) => (
    <Card hoverable size="small" onClick={() => navigate(`/diary/${diary.id}`)}>
      <h4 className="font-semibold truncate mb-1">{diary.title}</h4>
      <div className="text-gray-400 text-xs mb-2">
        <span>{diary.author_name}</span>
        {diary.destination && <span> · {diary.destination}</span>}
        <span> · 浏览 {diary.view_count}</span>
      </div>
      <div className="flex justify-between items-center mb-1">
        <Rate disabled value={diary.average_rating} allowHalf style={{ fontSize: 12 }} />
        <span className="text-xs text-gray-400">{diary.rating_count}人评 · {diary.comment_count}评论</span>
      </div>
      {diary.tags && diary.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1">
          {diary.tags.slice(0, 3).map((t, i) => <Tag key={i} className="text-xs">{t}</Tag>)}
        </div>
      )}
    </Card>
  )

  const tabItems = [
    { key: 'public', label: <span><BookOutlined /> 所有日记</span> },
    ...(user ? [{ key: 'my', label: <span><FireOutlined /> 我的日记</span> }] : []),
  ]

  return (
    <div>
      <Card className="mb-4">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <Space>
            <Search
              placeholder="搜索日记标题、目的地、作者..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
              enterButton
              style={{ width: 350 }}
            />
            <Select value={searchMode} onChange={setSearchMode} style={{ width: 120 }}>
              <Select.Option value="normal">普通搜索</Select.Option>
              <Select.Option value="fulltext">全文搜索</Select.Option>
            </Select>
          </Space>
          <Space>
            <Select value={sortBy} onChange={(v) => { setSortBy(v); setPage(1) }} style={{ width: 130 }}>
              <Select.Option value="mixed">综合推荐</Select.Option>
              <Select.Option value="popularity">按热度</Select.Option>
              <Select.Option value="rating">按评价</Select.Option>
            </Select>
            {user && (
              <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/diary/edit')}>
                写日记
              </Button>
            )}
          </Space>
        </div>
        {destination && (
          <div className="mt-2">
            <Tag color="blue" closable onClose={() => navigate('/diary')}>
              目的地: {destination}
            </Tag>
          </div>
        )}
      </Card>

      <Tabs activeKey={activeTab} onChange={(k) => { setActiveTab(k); setPage(1) }} items={tabItems} />

      <Spin spinning={loading}>
        {diaries.length === 0 && !loading ? (
          <Empty description="暂无日记" className="py-16">
            {user && <Button type="primary" onClick={() => navigate('/diary/edit')}>写第一篇日记</Button>}
          </Empty>
        ) : (
          <>
            <Row gutter={[16, 16]}>
              {diaries.map((d) => (
                <Col xs={24} sm={12} md={8} key={d.id}>
                  <DiaryCard diary={d} />
                </Col>
              ))}
            </Row>
            <div className="text-center mt-6">
              <Pagination current={page} total={total} pageSize={12}
                          onChange={(p) => setPage(p)} showTotal={(t) => `共 ${t} 条`} />
            </div>
          </>
        )}
      </Spin>
    </div>
  )
}

export default DiaryListPage
