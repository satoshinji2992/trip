/**
 * 景区/校园列表页 - 旅游推荐功能
 */
import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, Row, Col, Input, Select, Tag, Rate, Pagination, Spin, Empty, Space, Radio, Button } from 'antd'
import { SearchOutlined, FireOutlined, StarOutlined, EnvironmentOutlined } from '@ant-design/icons'
import { scenicAPI } from '../services/api'

const { Search } = Input

function ScenicListPage() {
  const [scenics, setScenics] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [searchParams, setSearchParams] = useSearchParams()
  const [sortBy, setSortBy] = useState('mixed')
  const [typeFilter, setTypeFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '')
  const navigate = useNavigate()

  const fetchData = async (queryText = searchParams.get('q') || '', pageNo = page) => {
    setLoading(true)
    try {
      let res
      if (queryText.trim()) {
        res = await scenicAPI.search({ q: queryText, page: pageNo, per_page: 12, sort_by: sortBy, type: typeFilter })
      } else {
        res = await scenicAPI.list({ page: pageNo, per_page: 12, sort_by: sortBy, type: typeFilter })
      }
      setScenics(res.data?.items || [])
      setTotal(res.data?.total || 0)
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  useEffect(() => {
    const q = searchParams.get('q') || ''
    setSearchQuery(q)
    fetchData(q, page)
  }, [searchParams, page, sortBy, typeFilter])

  const handleSearch = (value) => {
    setPage(1)
    if (value.trim()) {
      setSearchParams({ q: value })
    } else {
      setSearchParams({})
    }
  }

  return (
    <div>
      <Card className="mb-4">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <Search
            placeholder="搜索景区、校园名称、类别..."
            allowClear enterButton
            style={{ maxWidth: 400 }}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onSearch={handleSearch}
          />
          <Space wrap>
            <Radio.Group value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1) }}>
              <Radio.Button value="">全部</Radio.Button>
              <Radio.Button value="scenic">景区</Radio.Button>
              <Radio.Button value="campus">校园</Radio.Button>
            </Radio.Group>
            <Select value={sortBy} onChange={(v) => { setSortBy(v); setPage(1) }} style={{ width: 140 }}>
              <Select.Option value="mixed">综合推荐</Select.Option>
              <Select.Option value="popularity">按热度</Select.Option>
              <Select.Option value="rating">按评价</Select.Option>
            </Select>
          </Space>
        </div>
      </Card>

      <Spin spinning={loading}>
        {scenics.length === 0 && !loading ? (
          <Empty description="暂无数据" className="py-16" />
        ) : (
          <>
            <Row gutter={[16, 16]}>
              {scenics.map((s) => (
                <Col xs={24} sm={12} md={8} lg={6} key={s.id}>
                  <Card hoverable className="h-full" onClick={() => navigate(`/scenic/${s.id}`)}>
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-bold text-base truncate flex-1 m-0">{s.name}</h3>
                      <Tag color={s.type === 'campus' ? 'blue' : 'green'} className="ml-1 shrink-0">
                        {s.type === 'campus' ? '校园' : '景区'}
                      </Tag>
                    </div>
                    <Tag className="mb-2">{s.category}</Tag>
                    <p className="text-gray-400 text-xs mb-2 line-clamp-2">{s.description}</p>
                    <div className="flex items-center justify-between mb-1">
                      <Rate disabled value={s.rating} allowHalf style={{ fontSize: 12 }} />
                      <span className="text-xs text-gray-400">{s.rating_count}人评</span>
                    </div>
                    <div className="flex justify-between text-xs text-gray-500">
                      <span><FireOutlined className="text-red-400" /> {s.popularity}</span>
                      <span>{s.ticket_price > 0 ? `¥${s.ticket_price}` : '免费'}</span>
                    </div>
                    {s.tags && s.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {s.tags.slice(0, 3).map((t, i) => (
                          <Tag key={i} color="default" className="text-xs">{t}</Tag>
                        ))}
                      </div>
                    )}
                  </Card>
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

export default ScenicListPage
