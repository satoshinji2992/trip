/**
 * 首页 - 展示推荐景区、热门日记、系统功能入口
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Card, Row, Col, Input, Tag, Rate, Statistic, Carousel, Spin, Empty } from 'antd'
import {
  CompassOutlined, EnvironmentOutlined, BookOutlined, CoffeeOutlined,
  SearchOutlined, FireOutlined, StarOutlined,
} from '@ant-design/icons'
import { scenicAPI, diaryAPI } from '../services/api'

const { Search } = Input

function HomePage() {
  const [recommendScenics, setRecommendScenics] = useState([])
  const [hotDiaries, setHotDiaries] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      scenicAPI.recommend({ sort_by: 'mixed', top_k: 8 }).catch(() => ({ data: { items: [] } })),
      diaryAPI.public({ sort_by: 'popularity', per_page: 6 }).catch(() => ({ data: { items: [] } })),
    ]).then(([scenicRes, diaryRes]) => {
      setRecommendScenics(scenicRes.data?.items || [])
      setHotDiaries(diaryRes.data?.items || [])
    }).finally(() => setLoading(false))
  }, [])

  const features = [
    { icon: <CompassOutlined style={{ fontSize: 36, color: '#1890ff' }} />, title: '旅游推荐', desc: '智能推荐景区和校园，按热度、评价、兴趣排序', path: '/scenic' },
    { icon: <EnvironmentOutlined style={{ fontSize: 36, color: '#52c41a' }} />, title: '路线规划', desc: '最短路径规划，多点旅游线路，多种交通工具', path: '/scenic' },
    { icon: <BookOutlined style={{ fontSize: 36, color: '#722ed1' }} />, title: '旅游日记', desc: '记录旅行故事，浏览分享交流，全文搜索', path: '/diary' },
    { icon: <CoffeeOutlined style={{ fontSize: 36, color: '#fa541c' }} />, title: '美食推荐', desc: '发现周边美食，按菜系、热度、距离排序', path: '/food' },
  ]

  const handleSearch = (value) => {
    if (value.trim()) {
      navigate(`/scenic?q=${encodeURIComponent(value.trim())}`)
    }
  }

  return (
    <div>
      {/* Hero区域 */}
      <div className="text-center py-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl mb-8">
        <h1 className="text-4xl font-bold text-white mb-4">个性化旅游系统</h1>
        <p className="text-lg text-blue-100 mb-8">发现美景 · 规划路线 · 记录旅行 · 分享美食</p>
        <div className="max-w-lg mx-auto px-4">
          <Search
            placeholder="搜索景区、校园、目的地..."
            allowClear
            enterButton={<><SearchOutlined /> 搜索</>}
            size="large"
            onSearch={handleSearch}
          />
        </div>
      </div>

      {/* 功能入口 */}
      <Row gutter={[16, 16]} className="mb-8">
        {features.map((f, i) => (
          <Col xs={24} sm={12} md={6} key={i}>
            <Card hoverable className="text-center h-full" onClick={() => navigate(f.path)}>
              <div className="mb-3">{f.icon}</div>
              <h3 className="text-lg font-semibold mb-2">{f.title}</h3>
              <p className="text-gray-500 text-sm">{f.desc}</p>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 推荐景区 */}
      <Card title={<span><FireOutlined className="mr-2 text-red-500" />推荐景区/校园</span>} className="mb-8"
            extra={<a onClick={() => navigate('/scenic')}>查看全部</a>}>
        {loading ? <Spin /> : (
          <Row gutter={[16, 16]}>
            {recommendScenics.map((s) => (
              <Col xs={24} sm={12} md={6} key={s.id}>
                <Card hoverable size="small" onClick={() => navigate(`/scenic/${s.id}`)}>
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-semibold truncate flex-1">{s.name}</span>
                    <Tag color={s.type === 'campus' ? 'blue' : 'green'} className="ml-1">
                      {s.type === 'campus' ? '校园' : '景区'}
                    </Tag>
                  </div>
                  <div className="text-gray-400 text-xs mb-1">{s.category}</div>
                  <div className="flex justify-between items-center">
                    <Rate disabled defaultValue={s.rating} allowHalf style={{ fontSize: 12 }} />
                    <span className="text-xs text-gray-400"><FireOutlined /> {s.popularity}</span>
                  </div>
                  {s.ticket_price > 0 && (
                    <div className="text-orange-500 text-sm mt-1">¥{s.ticket_price}</div>
                  )}
                </Card>
              </Col>
            ))}
            {recommendScenics.length === 0 && <Empty description="暂无推荐数据" className="w-full py-8" />}
          </Row>
        )}
      </Card>

      {/* 热门日记 */}
      <Card title={<span><StarOutlined className="mr-2 text-yellow-500" />热门旅游日记</span>}
            extra={<a onClick={() => navigate('/diary')}>查看全部</a>}>
        {loading ? <Spin /> : (
          <Row gutter={[16, 16]}>
            {hotDiaries.map((d) => (
              <Col xs={24} sm={12} md={8} key={d.id}>
                <Card hoverable size="small" onClick={() => navigate(`/diary/${d.id}`)}>
                  <h4 className="font-semibold truncate mb-1">{d.title}</h4>
                  <div className="text-gray-400 text-xs mb-2">
                    {d.author_name} · {d.destination} · 浏览 {d.view_count}
                  </div>
                  <div className="flex justify-between">
                    <Rate disabled defaultValue={d.average_rating} allowHalf style={{ fontSize: 12 }} />
                    <span className="text-xs text-gray-400">{d.comment_count} 评论</span>
                  </div>
                </Card>
              </Col>
            ))}
            {hotDiaries.length === 0 && <Empty description="暂无日记" className="w-full py-8" />}
          </Row>
        )}
      </Card>
    </div>
  )
}

export default HomePage
