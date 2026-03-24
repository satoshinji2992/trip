/**
 * 室内导航页 - 建筑内部导航，包括电梯、楼梯、房间导航
 */
import React, { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Row, Col, Select, Button, Tag, Steps, Spin, Empty, Space, message, Tabs, Divider } from 'antd'
import { CompassOutlined, HomeOutlined } from '@ant-design/icons'
import { navAPI } from '../services/api'

function IndoorNavPage() {
  const { buildingId } = useParams()
  const [building, setBuilding] = useState(null)
  const [floorsData, setFloorsData] = useState({})
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [loading, setLoading] = useState(true)
  const [fromNode, setFromNode] = useState(null)
  const [toNode, setToNode] = useState(null)
  const [navResult, setNavResult] = useState(null)
  const [calculating, setCalculating] = useState(false)
  const canvasRef = useRef(null)

  useEffect(() => {
    navAPI.buildingInfo(buildingId)
      .then(res => {
        const d = res.data
        setBuilding(d.building)
        setFloorsData(d.floors || {})
        setNodes(d.nodes || [])
        setEdges(d.edges || [])
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [buildingId])

  useEffect(() => { drawFloorPlan() }, [nodes, navResult])

  const drawFloorPlan = () => {
    const canvas = canvasRef.current
    if (!canvas || nodes.length === 0) return
    const ctx = canvas.getContext('2d')
    const W = canvas.width = 800
    const H = canvas.height = 500
    ctx.clearRect(0, 0, W, H)
    ctx.fillStyle = '#fafafa'
    ctx.fillRect(0, 0, W, H)

    const nodeMap = {}
    nodes.forEach(n => { nodeMap[n.id] = n })

    // 按楼层偏移绘制节点
    const floorOffset = {}
    const floorNums = [...new Set(nodes.map(n => n.floor))].sort((a, b) => a - b)
    floorNums.forEach((f, i) => { floorOffset[f] = i * 120 + 50 })

    // 绘制边
    ctx.strokeStyle = '#d9d9d9'
    ctx.lineWidth = 1
    edges.forEach(e => {
      const from = nodeMap[e.from_node_id]
      const to = nodeMap[e.to_node_id]
      if (from && to) {
        const fy = floorOffset[from.floor] || 50
        const ty = floorOffset[to.floor] || 50
        ctx.strokeStyle = e.edge_type === 'elevator' ? '#1890ff' : e.edge_type === 'stair' ? '#52c41a' : '#d9d9d9'
        ctx.lineWidth = e.edge_type === 'corridor' ? 1 : 2
        ctx.beginPath()
        ctx.moveTo(from.x * 3 + 100, fy + from.y * 0.5)
        ctx.lineTo(to.x * 3 + 100, ty + to.y * 0.5)
        ctx.stroke()
      }
    })

    // 绘制导航路径
    if (navResult && navResult.path) {
      const path = navResult.path
      ctx.strokeStyle = '#ff4d4f'
      ctx.lineWidth = 3
      ctx.setLineDash([6, 3])
      ctx.beginPath()
      for (let i = 0; i < path.length; i++) {
        const n = nodeMap[path[i]]
        if (n) {
          const ny = floorOffset[n.floor] || 50
          const nx = n.x * 3 + 100
          const nny = ny + n.y * 0.5
          i === 0 ? ctx.moveTo(nx, nny) : ctx.lineTo(nx, nny)
        }
      }
      ctx.stroke()
      ctx.setLineDash([])
    }

    // 绘制节点
    const typeColors = { entrance: '#52c41a', elevator: '#1890ff', stair: '#fa8c16', room: '#722ed1', corridor: '#999' }
    nodes.forEach(n => {
      const ny = floorOffset[n.floor] || 50
      const nx = n.x * 3 + 100
      const nny = ny + n.y * 0.5
      const isFrom = n.id === fromNode
      const isTo = n.id === toNode
      ctx.beginPath()
      ctx.arc(nx, nny, isFrom || isTo ? 8 : 5, 0, Math.PI * 2)
      ctx.fillStyle = isFrom ? '#52c41a' : isTo ? '#f5222d' : (typeColors[n.node_type] || '#1890ff')
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()
      ctx.fillStyle = '#333'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(n.name, nx, nny - 10)
    })

    // 绘制楼层标签
    ctx.fillStyle = '#666'
    ctx.font = 'bold 14px sans-serif'
    ctx.textAlign = 'left'
    floorNums.forEach(f => {
      ctx.fillText(`${f}F`, 20, floorOffset[f] + 30)
    })
  }

  const calcPath = async () => {
    if (!fromNode || !toNode) { message.warning('请选择起点和终点'); return }
    setCalculating(true)
    try {
      const res = await navAPI.indoorPath({ building_id: parseInt(buildingId), from_node_id: fromNode, to_node_id: toNode })
      setNavResult(res.data)
      message.success(`导航路径规划完成！距离: ${res.data.total_distance}米`)
    } catch (e) { message.error('路径规划失败') }
    setCalculating(false)
  }

  if (loading) return <Spin size="large" className="flex justify-center py-20" />
  if (!building) return <Empty description="建筑不存在" />

  const nodeTypeMap = { entrance: '入口', elevator: '电梯', stair: '楼梯', room: '房间', corridor: '走廊' }

  return (
    <div>
      <Card className="mb-4">
        <h2 className="text-xl font-bold mb-2">
          <HomeOutlined className="mr-2" />{building.name} - 室内导航
        </h2>
        <Space>
          <Tag>{building.floors}层</Tag>
          <Tag color={building.has_elevator ? 'green' : 'default'}>{building.has_elevator ? '有电梯' : '无电梯'}</Tag>
          <Tag>节点: {nodes.length}</Tag>
        </Space>
      </Card>

      <Row gutter={16}>
        <Col xs={24} md={16}>
          <Card title="楼层平面图" size="small">
            <canvas ref={canvasRef} style={{ width: '100%', height: 400 }} className="map-canvas" />
            <div className="text-xs text-gray-400 mt-2">
              <span className="inline-block w-3 h-3 rounded-full mr-1" style={{ background: '#52c41a' }} /> 入口
              <span className="inline-block w-3 h-3 rounded-full ml-3 mr-1" style={{ background: '#1890ff' }} /> 电梯
              <span className="inline-block w-3 h-3 rounded-full ml-3 mr-1" style={{ background: '#fa8c16' }} /> 楼梯
              <span className="inline-block w-3 h-3 rounded-full ml-3 mr-1" style={{ background: '#722ed1' }} /> 房间
              <span className="text-red-500 ml-3">--- 导航路径</span>
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="导航" size="small" className="mb-4">
            <div className="mb-3">
              <div className="text-sm font-semibold mb-1">起点</div>
              <Select placeholder="选择起点" className="w-full" showSearch optionFilterProp="label"
                      value={fromNode} onChange={setFromNode}
                      options={nodes.map(n => ({ value: n.id, label: `${n.name} (${n.floor}F ${nodeTypeMap[n.node_type] || ''})` }))} />
            </div>
            <div className="mb-3">
              <div className="text-sm font-semibold mb-1">终点</div>
              <Select placeholder="选择终点" className="w-full" showSearch optionFilterProp="label"
                      value={toNode} onChange={setToNode}
                      options={nodes.map(n => ({ value: n.id, label: `${n.name} (${n.floor}F ${nodeTypeMap[n.node_type] || ''})` }))} />
            </div>
            <Button type="primary" block loading={calculating} onClick={calcPath} icon={<CompassOutlined />}>
              开始导航
            </Button>
          </Card>

          {navResult && (
            <Card title="导航结果" size="small">
              <p><strong>总距离:</strong> {navResult.total_distance}米</p>
              <Divider className="my-2" />
              <div className="text-sm font-semibold mb-2">导航步骤:</div>
              <Steps direction="vertical" size="small" current={-1}
                items={(navResult.navigation_steps || []).map((step, i) => ({
                  title: step.instruction,
                  description: step.type === 'elevator' ? '乘坐电梯' : step.type === 'stair' ? '走楼梯' : '步行',
                  status: 'process',
                }))}
              />
            </Card>
          )}
        </Col>
      </Row>
    </div>
  )
}

export default IndoorNavPage
