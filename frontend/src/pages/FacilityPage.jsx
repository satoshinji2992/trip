/**
 * 场所查询页 - 附近设施查找、距离排序
 */
import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Row, Col, Select, Input, Tag, Rate, List, Spin, Empty, Space, message } from 'antd'
import { SearchOutlined, EnvironmentOutlined } from '@ant-design/icons'
import { facilityAPI, routeAPI } from '../services/api'

const { Search } = Input

function FacilityPage() {
  const { scenicId } = useParams()
  const [facilities, setFacilities] = useState([])
  const [nodes, setNodes] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedNode, setSelectedNode] = useState(null)
  const [typeFilter, setTypeFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [facilityTypes, setFacilityTypes] = useState([])

  useEffect(() => {
    setLoading(true)
    Promise.all([
      routeAPI.nodes({ scenic_id: scenicId }),
      facilityAPI.types(),
      facilityAPI.byCategory({ scenic_id: scenicId }),
    ]).then(([nodesRes, typesRes, facilitiesRes]) => {
      setNodes(nodesRes.data || [])
      setFacilityTypes(typesRes.data || [])
      setFacilities(facilitiesRes.data?.items || [])
      if ((nodesRes.data || []).length > 0) setSelectedNode((nodesRes.data || [])[0].id)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [scenicId])

  const handleSearch = async () => {
    if (!searchQuery.trim()) { message.warning('请输入搜索关键词'); return }
    setLoading(true)
    try {
      const res = await facilityAPI.search({
        scenic_id: scenicId, q: searchQuery, node_id: selectedNode || undefined,
      })
      setFacilities(res.data?.items || [])
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  const handleNearby = async () => {
    if (!selectedNode) { message.warning('请先选择当前位置'); return }
    setLoading(true)
    try {
      const res = await facilityAPI.nearby({
        scenic_id: scenicId, node_id: selectedNode,
        type: typeFilter || undefined, max_distance: 10000,
      })
      setFacilities(res.data?.items || [])
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  const handleCategoryFilter = async (type) => {
    setTypeFilter(type)
    setLoading(true)
    try {
      const res = await facilityAPI.byCategory({ scenic_id: scenicId, category: type || undefined })
      setFacilities(res.data?.items || [])
    } catch (e) { /* ignore */ }
    setLoading(false)
  }

  const facilityTypeMap = {
    shop: '商店', restaurant: '饭店', restroom: '洗手间', library: '图书馆',
    canteen: '食堂', supermarket: '超市', cafe: '咖啡馆', hospital: '医务室',
    atm: 'ATM', parking: '停车场',
  }

  return (
    <div>
      <Card className="mb-4">
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <div className="text-sm font-semibold mb-1">当前位置</div>
            <Select
              placeholder="选择您的当前位置（节点）"
              className="w-full"
              showSearch
              optionFilterProp="label"
              value={selectedNode}
              onChange={(v) => setSelectedNode(v)}
              options={nodes.map(n => ({ value: n.id, label: n.name }))}
              allowClear
            />
          </Col>
          <Col xs={24} md={8}>
            <div className="text-sm font-semibold mb-1">搜索设施</div>
            <Search
              placeholder="输入类别名称、设施名称..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
              enterButton
            />
          </Col>
          <Col xs={24} md={8}>
            <div className="text-sm font-semibold mb-1">类别过滤</div>
            <Select
              placeholder="选择设施类别"
              className="w-full"
              value={typeFilter}
              onChange={handleCategoryFilter}
              allowClear
              onClear={() => handleCategoryFilter('')}
            >
              <Select.Option value="">全部类别</Select.Option>
              {facilityTypes.map(t => (
                <Select.Option key={t.value} value={t.value}>{t.label}</Select.Option>
              ))}
            </Select>
          </Col>
        </Row>
        <div className="mt-3">
          <Space>
            <button className="ant-btn ant-btn-primary ant-btn-sm" onClick={handleNearby}>
              <EnvironmentOutlined /> 查找附近设施
            </button>
            <span className="text-xs text-gray-400">提示：选择当前位置后，结果将按实际路径距离排序（非直线距离）</span>
          </Space>
        </div>
      </Card>

      <Spin spinning={loading}>
        {facilities.length === 0 && !loading ? (
          <Empty description="请选择位置或搜索设施" className="py-16" />
        ) : (
          <Row gutter={[16, 16]}>
            {facilities.map((f, i) => (
              <Col xs={24} sm={12} md={8} key={f.id || i}>
                <Card size="small" hoverable>
                  <div className="flex justify-between items-start mb-1">
                    <span className="font-semibold">{f.name}</span>
                    <Tag color="orange">{facilityTypeMap[f.type] || f.type}</Tag>
                  </div>
                  {f.description && <p className="text-xs text-gray-500 mb-1">{f.description}</p>}
                  <div className="flex justify-between items-center">
                    <Rate disabled value={f.rating} allowHalf style={{ fontSize: 11 }} />
                    <span className="text-xs text-gray-400">{f.open_time}</span>
                  </div>
                  {f.distance !== undefined && f.distance !== Infinity && (
                    <div className="mt-1 text-sm text-blue-500">
                      <EnvironmentOutlined /> 路径距离: {Math.round(f.distance)}米
                    </div>
                  )}
                </Card>
              </Col>
            ))}
          </Row>
        )}
      </Spin>
    </div>
  )
}

export default FacilityPage
