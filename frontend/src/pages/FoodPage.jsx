/**
 * 美食推荐页 - 核心算法为模糊查找和排序算法
 */
import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, Row, Col, Input, Select, Tag, Rate, Spin, Empty, Space, message, Tabs, List } from 'antd'
import { CoffeeOutlined, FireOutlined, EnvironmentOutlined, DollarOutlined } from '@ant-design/icons'
import { foodAPI, routeAPI, scenicAPI } from '../services/api'

const { Search } = Input

function FoodPage() {
  const [searchParams] = useSearchParams()
  const initScenicId = searchParams.get('scenic_id') || ''
  const [scenicId, setScenicId] = useState(initScenicId)
  const [scenicOptions, setScenicOptions] = useState([])
  const [restaurants, setRestaurants] = useState([])
  const [foods, setFoods] = useState([])
  const [nodes, setNodes] = useState([])
  const [loading, setLoading] = useState(false)
  const [sortBy, setSortBy] = useState('mixed')
  const [cuisine, setCuisine] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedNode, setSelectedNode] = useState(null)
  const [cuisineOptions, setCuisineOptions] = useState([])

  useEffect(() => {
    scenicAPI.list({ per_page: 200 })
      .then(res => {
        const options = (res.data?.items || []).map(s => ({ value: String(s.id), label: s.name }))
        setScenicOptions(options)
        if (!scenicId && options.length > 0) setScenicId(options[0].value)
      })
      .catch(() => {})
    foodAPI.cuisines()
      .then(res => setCuisineOptions(res.data || []))
      .catch(() => {})
  }, [])

  useEffect(() => {
    if (scenicId) {
      routeAPI.nodes({ scenic_id: scenicId })
        .then(res => setNodes(res.data || []))
        .catch(() => {})
      fetchRecommend()
    }
  }, [scenicId, sortBy, cuisine])

  const fetchRecommend = async () => {
    if (!scenicId) return
    setLoading(true)
    try {
      const res = await foodAPI.recommend({
        scenic_id: scenicId, sort_by: sortBy, cuisine: cuisine || undefined,
        top_k: 20, node_id: selectedNode || undefined,
      })
      setRestaurants(res.data?.items || [])
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  const handleSearch = async () => {
    if (!scenicId) { message.warning('请先选择景区/校园'); return }
    if (!searchQuery.trim()) { message.warning('请输入搜索关键词'); return }
    setLoading(true)
    try {
      const res = await foodAPI.search({
        scenic_id: scenicId, q: searchQuery, sort_by: sortBy,
        node_id: selectedNode || undefined,
      })
      setRestaurants(res.data?.restaurants || [])
      setFoods(res.data?.foods || [])
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  const cuisineMap = { chinese: '中餐', western: '西餐', japanese: '日料', korean: '韩餐', fast_food: '快餐', snack: '小吃', cafe: '咖啡甜品', other: '其他' }

  const RestaurantCard = ({ r }) => (
    <Card size="small" hoverable>
      <div className="flex justify-between items-start mb-1">
        <span className="font-semibold">{r.name}</span>
        <Tag color="orange">{cuisineMap[r.cuisine] || r.cuisine}</Tag>
      </div>
      <p className="text-xs text-gray-500 mb-1 line-clamp-2">{r.description}</p>
      <div className="flex justify-between items-center mb-1">
        <Rate disabled value={r.rating} allowHalf style={{ fontSize: 11 }} />
        <span className="text-xs text-gray-400">{r.rating_count}人评</span>
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span><DollarOutlined /> 人均 ¥{r.avg_price}</span>
        <span><FireOutlined className="text-red-400" /> {r.popularity}</span>
      </div>
      {r.distance !== undefined && r.distance !== Infinity && r.distance > 0 && (
        <div className="mt-1 text-sm text-blue-500">
          <EnvironmentOutlined /> {Math.round(r.distance)}米
        </div>
      )}
    </Card>
  )

  return (
    <div>
      <Card className="mb-4">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={6}>
            <div className="text-sm font-semibold mb-1">景区/校园</div>
            <Select placeholder="选择景区或校园" className="w-full" showSearch optionFilterProp="label"
                    value={scenicId || undefined} onChange={setScenicId} options={scenicOptions} />
          </Col>
          <Col xs={24} md={5}>
            <div className="text-sm font-semibold mb-1">当前位置</div>
            <Select placeholder="选择位置(可选)" className="w-full" showSearch optionFilterProp="label"
                    value={selectedNode} onChange={setSelectedNode} allowClear
                    options={nodes.map(n => ({ value: n.id, label: n.name }))} />
          </Col>
          <Col xs={24} md={4}>
            <div className="text-sm font-semibold mb-1">菜系</div>
            <Select placeholder="全部菜系" className="w-full" value={cuisine}
                    onChange={setCuisine} allowClear>
              <Select.Option value="">全部</Select.Option>
              {cuisineOptions.map(c => <Select.Option key={c.value} value={c.value}>{c.label}</Select.Option>)}
            </Select>
          </Col>
          <Col xs={24} md={4}>
            <div className="text-sm font-semibold mb-1">排序</div>
            <Select value={sortBy} onChange={setSortBy} className="w-full">
              <Select.Option value="mixed">综合推荐</Select.Option>
              <Select.Option value="popularity">按热度</Select.Option>
              <Select.Option value="rating">按评价</Select.Option>
              <Select.Option value="distance">按距离</Select.Option>
            </Select>
          </Col>
          <Col xs={24} md={5}>
            <div className="text-sm font-semibold mb-1">搜索</div>
            <Search placeholder="美食名称、菜系、饭店..." value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)} onSearch={handleSearch} enterButton />
          </Col>
        </Row>
      </Card>

      <Spin spinning={loading}>
        {!scenicId ? (
          <Empty description="请先选择景区/校园" className="py-16" />
        ) : restaurants.length === 0 && !loading ? (
          <Empty description="暂无美食数据" className="py-16" />
        ) : (
          <Tabs defaultActiveKey="restaurants" items={[
            {
              key: 'restaurants',
              label: `餐厅 (${restaurants.length})`,
              children: (
                <Row gutter={[16, 16]}>
                  {restaurants.map((r) => (
                    <Col xs={24} sm={12} md={8} lg={6} key={r.id}>
                      <RestaurantCard r={r} />
                    </Col>
                  ))}
                </Row>
              ),
            },
            ...(foods.length > 0 ? [{
              key: 'foods',
              label: `菜品 (${foods.length})`,
              children: (
                <Row gutter={[16, 16]}>
                  {foods.map((f, i) => (
                    <Col xs={24} sm={12} md={8} lg={6} key={f.id || i}>
                      <Card size="small">
                        <div className="font-semibold">{f.name}</div>
                        <div className="text-xs text-gray-400">{f.restaurant_name}</div>
                        <div className="flex justify-between mt-1">
                          <Rate disabled value={f.rating} allowHalf style={{ fontSize: 11 }} />
                          <span className="text-orange-500">¥{f.price}</span>
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              ),
            }] : []),
          ]} />
        )}
      </Spin>
    </div>
  )
}

export default FoodPage
