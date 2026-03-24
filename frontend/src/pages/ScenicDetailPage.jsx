/**
 * 景区/校园详情页 - 展示详情，入口到路线规划、场所查询、美食推荐等
 */
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Card, Descriptions, Tag, Rate, Button, Row, Col, List, Spin, Empty, Space, Tabs, Divider } from 'antd'
import {
  EnvironmentOutlined, FireOutlined, ClockCircleOutlined, DollarOutlined,
  CompassOutlined, SearchOutlined, CoffeeOutlined, HomeOutlined, BankOutlined,
} from '@ant-design/icons'
import { scenicAPI } from '../services/api'

function ScenicDetailPage() {
  const { id } = useParams()
  const [scenic, setScenic] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    scenicAPI.detail(id)
      .then((res) => setScenic(res.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <Spin size="large" className="flex justify-center py-20" />
  if (!scenic) return <Empty description="景区/校园不存在" />

  const buildingTypeMap = {
    attraction: '景点', teaching: '教学楼', office: '办公楼',
    dormitory: '宿舍楼', library: '图书馆', museum: '博物馆', other: '其他',
  }

  const facilityTypeMap = {
    shop: '商店', restaurant: '饭店', restroom: '洗手间', library: '图书馆',
    canteen: '食堂', supermarket: '超市', cafe: '咖啡馆', hospital: '医务室',
    atm: 'ATM', parking: '停车场',
  }

  return (
    <div>
      <Card className="mb-4">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-2xl font-bold mb-2">
              {scenic.name}
              <Tag color={scenic.type === 'campus' ? 'blue' : 'green'} className="ml-3">
                {scenic.type === 'campus' ? '校园' : '景区'}
              </Tag>
              <Tag>{scenic.category}</Tag>
            </h1>
            <p className="text-gray-500 mb-2"><EnvironmentOutlined className="mr-1" />{scenic.address}</p>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-orange-500 mb-1">
              {scenic.ticket_price > 0 ? `¥${scenic.ticket_price}` : '免费'}
            </div>
            <Rate disabled value={scenic.rating} allowHalf />
            <div className="text-xs text-gray-400 mt-1">{scenic.rating_count}人评价</div>
          </div>
        </div>
        <p className="text-gray-600 mb-4">{scenic.description}</p>
        <Row gutter={16}>
          <Col span={6}><Descriptions.Item><FireOutlined className="mr-1 text-red-500" />热度: {scenic.popularity}</Descriptions.Item></Col>
          <Col span={6}><ClockCircleOutlined className="mr-1" />{scenic.open_time}</Col>
          <Col span={6}>建筑物: {scenic.building_count}个</Col>
          <Col span={6}>服务设施: {scenic.facility_count}个</Col>
        </Row>
        {scenic.tags && scenic.tags.length > 0 && (
          <div className="mt-3">
            {scenic.tags.map((t, i) => <Tag key={i} color="processing">{t}</Tag>)}
          </div>
        )}
      </Card>

      {/* 功能入口 */}
      <Row gutter={[16, 16]} className="mb-4">
        <Col xs={12} md={6}>
          <Card hoverable className="text-center" onClick={() => navigate(`/route/${scenic.id}`)}>
            <CompassOutlined style={{ fontSize: 28, color: '#1890ff' }} />
            <div className="mt-2 font-semibold">路线规划</div>
            <div className="text-xs text-gray-400">最短路径 · 多点规划</div>
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card hoverable className="text-center" onClick={() => navigate(`/facility/${scenic.id}`)}>
            <SearchOutlined style={{ fontSize: 28, color: '#52c41a' }} />
            <div className="mt-2 font-semibold">场所查询</div>
            <div className="text-xs text-gray-400">附近设施 · 距离排序</div>
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card hoverable className="text-center" onClick={() => navigate(`/food?scenic_id=${scenic.id}`)}>
            <CoffeeOutlined style={{ fontSize: 28, color: '#fa541c' }} />
            <div className="mt-2 font-semibold">美食推荐</div>
            <div className="text-xs text-gray-400">周边美食 · 菜系筛选</div>
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card hoverable className="text-center" onClick={() => navigate(`/diary?destination=${scenic.name}`)}>
            <BankOutlined style={{ fontSize: 28, color: '#722ed1' }} />
            <div className="mt-2 font-semibold">旅游日记</div>
            <div className="text-xs text-gray-400">游记攻略 · 交流分享</div>
          </Card>
        </Col>
      </Row>

      {/* 建筑物和设施列表 */}
      <Tabs defaultActiveKey="buildings" items={[
        {
          key: 'buildings',
          label: `建筑物 (${scenic.buildings?.length || 0})`,
          children: (
            <Row gutter={[16, 16]}>
              {(scenic.buildings || []).map((b) => (
                <Col xs={24} sm={12} md={8} key={b.id}>
                  <Card size="small" hoverable onClick={() => navigate(`/indoor/${b.id}`)}>
                    <div className="flex justify-between">
                      <span className="font-semibold">{b.name}</span>
                      <Tag>{buildingTypeMap[b.type] || b.type}</Tag>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {b.floors}层 {b.has_elevator ? '· 有电梯' : '· 无电梯'}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">{b.description}</div>
                  </Card>
                </Col>
              ))}
              {(!scenic.buildings || scenic.buildings.length === 0) && <Empty description="暂无建筑物数据" className="w-full py-8" />}
            </Row>
          ),
        },
        {
          key: 'facilities',
          label: `服务设施 (${scenic.facilities?.length || 0})`,
          children: (
            <Row gutter={[16, 16]}>
              {(scenic.facilities || []).map((f) => (
                <Col xs={24} sm={12} md={8} key={f.id}>
                  <Card size="small">
                    <div className="flex justify-between">
                      <span className="font-semibold">{f.name}</span>
                      <Tag color="orange">{facilityTypeMap[f.type] || f.type}</Tag>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">{f.open_time}</div>
                    <Rate disabled value={f.rating} allowHalf style={{ fontSize: 10 }} />
                  </Card>
                </Col>
              ))}
              {(!scenic.facilities || scenic.facilities.length === 0) && <Empty description="暂无设施数据" className="w-full py-8" />}
            </Row>
          ),
        },
      ]} />
    </div>
  )
}

export default ScenicDetailPage
