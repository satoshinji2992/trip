/**
 * 路线规划页 - 最短路径、多点路线、地图展示
 */
import React, { useState, useEffect, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { Card, Row, Col, Select, Button, Radio, Tag, List, Spin, Empty, Space, message, Checkbox, Divider, Steps } from 'antd'
import { CompassOutlined, AimOutlined, SwapOutlined, CarOutlined, NodeIndexOutlined } from '@ant-design/icons'
import { routeAPI } from '../services/api'

const MAX_RENDER_NODES = 120
const MAX_RENDER_EDGES = 600
const MAX_LABEL_NODES = 25

function pickRenderItems(nodes, edges, selectedIds) {
  const importantIds = new Set(selectedIds.filter(Boolean))
  const sampledNodes = sampleWithPriority(nodes, MAX_RENDER_NODES, importantIds)
  const priorityEdges = []
  const normalEdges = []
  edges.forEach((edge) => {
    if (importantIds.has(edge.from_node_id) || importantIds.has(edge.to_node_id)) priorityEdges.push(edge)
    else normalEdges.push(edge)
  })
  const sampledEdges = sampleWithPriority([...priorityEdges, ...normalEdges], MAX_RENDER_EDGES, new Set(priorityEdges.map((edge) => edge.id)))

  return {
    nodes: sampledNodes,
    edges: sampledEdges,
    simplified: sampledNodes.length < nodes.length || sampledEdges.length < edges.length,
  }
}

function sampleWithPriority(items, limit, priorityIds = new Set()) {
  if (items.length <= limit) return items

  const priorityItems = []
  const normalItems = []
  items.forEach((item) => {
    if (priorityIds.has(item.id)) priorityItems.push(item)
    else normalItems.push(item)
  })

  const remaining = Math.max(limit - priorityItems.length, 0)
  if (remaining === 0) return priorityItems.slice(0, limit)

  const step = Math.max(1, Math.ceil(normalItems.length / remaining))
  const sampled = []
  for (let i = 0; i < normalItems.length && sampled.length < remaining; i += step) {
    sampled.push(normalItems[i])
  }

  return [...priorityItems, ...sampled].slice(0, limit)
}

function pickLabelNodeIds(nodes, selectedIds) {
  const importantIds = new Set(selectedIds.filter(Boolean))
  const labelCandidates = nodes.filter((node) => importantIds.has(node.id) || isUsefulNodeLabel(node.name))
  const sampledNodes = sampleWithPriority(labelCandidates, MAX_LABEL_NODES, importantIds)
  return new Set(sampledNodes.map((node) => node.id))
}

function isUsefulNodeLabel(name = '') {
  if (!name) return false
  if (/^路口\d+$/.test(name)) return false
  if (/出入口\d+$/.test(name)) return false
  return true
}

function congestionColor(congestion = 0) {
  if (congestion >= 0.75) return '#ff4d4f'
  if (congestion >= 0.45) return '#faad14'
  return '#52c41a'
}

function congestionLabel(congestion = 0) {
  if (congestion >= 0.75) return '拥挤'
  if (congestion >= 0.45) return '较忙'
  return '畅通'
}

function RoutePlanPage() {
  const { scenicId } = useParams()
  const [mapData, setMapData] = useState({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const [fromNode, setFromNode] = useState(null)
  const [toNode, setToNode] = useState(null)
  const [multiDests, setMultiDests] = useState([])
  const [strategy, setStrategy] = useState('distance')
  const [transport, setTransport] = useState('walk')
  const [transportOptions, setTransportOptions] = useState([])
  const [pathResult, setPathResult] = useState(null)
  const [multiResult, setMultiResult] = useState(null)
  const [planMode, setPlanMode] = useState('single')
  const [calculating, setCalculating] = useState(false)
  const [returnToStart, setReturnToStart] = useState(true)
  const canvasRef = useRef(null)

  useEffect(() => {
    Promise.all([
      routeAPI.mapData({ scenic_id: scenicId }),
      routeAPI.transportOptions({ scenic_id: scenicId }),
    ]).then(([mapRes, transRes]) => {
      setMapData(mapRes.data || { nodes: [], edges: [] })
      setTransportOptions(transRes.data || [])
      if (transRes.data?.length > 0) setTransport(transRes.data[0].value)
    }).catch(() => {}).finally(() => setLoading(false))
  }, [scenicId])

  useEffect(() => { drawMap() }, [mapData, pathResult, multiResult])

  const drawMap = () => {
    const canvas = canvasRef.current
    if (!canvas || mapData.nodes.length === 0) return
    const ctx = canvas.getContext('2d')
    const W = canvas.width = 1000
    const H = canvas.height = 700
    ctx.clearRect(0, 0, W, H)
    ctx.fillStyle = '#fafafa'
    ctx.fillRect(0, 0, W, H)

    const nodeMap = {}
    mapData.nodes.forEach(n => { nodeMap[n.id] = n })
    const activePathNodes = new Set((pathResult?.path || multiResult?.ordered_path || []))
    const selectedIds = [fromNode, toNode, ...multiDests, ...activePathNodes]
    const renderData = pickRenderItems(mapData.nodes, mapData.edges, selectedIds)
    const labelNodeIds = pickLabelNodeIds(renderData.nodes, selectedIds)

    ctx.lineWidth = renderData.simplified ? 1 : 1.5
    renderData.edges.forEach(e => {
      const from = nodeMap[e.from_node_id]
      const to = nodeMap[e.to_node_id]
      if (from && to) {
        ctx.strokeStyle = congestionColor(e.congestion)
        ctx.globalAlpha = 0.45
        ctx.beginPath()
        ctx.moveTo(from.x, from.y)
        ctx.lineTo(to.x, to.y)
        ctx.stroke()
        ctx.globalAlpha = 1
      }
    })

    // 绘制路径高亮
    const result = planMode === 'single' ? pathResult : multiResult
    if (result) {
      const pathNodes = result.path || result.ordered_path || []
      if (pathNodes.length > 1) {
        ctx.strokeStyle = '#1890ff'
        ctx.lineWidth = 4
        ctx.setLineDash([8, 4])
        ctx.beginPath()
        for (let i = 0; i < pathNodes.length; i++) {
          const n = nodeMap[pathNodes[i]]
          if (n) { i === 0 ? ctx.moveTo(n.x, n.y) : ctx.lineTo(n.x, n.y) }
        }
        ctx.stroke()
        ctx.setLineDash([])
      }
    }

    // 绘制节点
    renderData.nodes.forEach(n => {
      const isFrom = n.id === fromNode
      const isTo = n.id === toNode
      const isDest = multiDests.includes(n.id)
      ctx.beginPath()
      ctx.arc(n.x, n.y, isFrom || isTo || isDest ? 8 : (renderData.simplified ? 4 : 5), 0, Math.PI * 2)
      ctx.fillStyle = isFrom ? '#52c41a' : isTo ? '#f5222d' : isDest ? '#fa8c16' : '#1890ff'
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()
      if (labelNodeIds.has(n.id)) {
        ctx.fillStyle = '#333'
        ctx.font = '11px sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(n.name, n.x, n.y - 12)
      }
    })
  }

  const handleCanvasClick = (e) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const x = (e.clientX - rect.left) * (canvas.width / rect.width)
    const y = (e.clientY - rect.top) * (canvas.height / rect.height)

    let nearest = null, minDist = Infinity
    mapData.nodes.forEach(n => {
      const d = Math.sqrt((n.x - x) ** 2 + (n.y - y) ** 2)
      if (d < minDist && d < 20) { minDist = d; nearest = n }
    })
    if (!nearest) return

    if (planMode === 'single') {
      if (!fromNode) { setFromNode(nearest.id); message.info(`起点: ${nearest.name}`) }
      else if (!toNode) { setToNode(nearest.id); message.info(`终点: ${nearest.name}`) }
      else { setFromNode(nearest.id); setToNode(null); setPathResult(null); message.info(`重新选择起点: ${nearest.name}`) }
    } else {
      if (!fromNode) { setFromNode(nearest.id); message.info(`起点: ${nearest.name}`) }
      else if (!multiDests.includes(nearest.id) && nearest.id !== fromNode) {
        setMultiDests([...multiDests, nearest.id]); message.info(`添加目的地: ${nearest.name}`)
      }
    }
  }

  const calcSingle = async () => {
    if (!fromNode || !toNode) { message.warning('请选择起点和终点'); return }
    setCalculating(true)
    try {
      const res = await routeAPI.shortest({ scenic_id: parseInt(scenicId), from_node_id: fromNode, to_node_id: toNode, strategy, transport })
      setPathResult(res.data)
      message.success(`路径规划完成！${strategy === 'distance' ? '距离' : '时间'}: ${res.data.total_cost} ${res.data.cost_unit}`)
    } catch (e) { message.error(e.message || '路径规划失败') }
    setCalculating(false)
  }

  const calcMulti = async () => {
    if (!fromNode || multiDests.length === 0) { message.warning('请选择起点和至少一个目的地'); return }
    setCalculating(true)
    try {
      const res = await routeAPI.multi({
        scenic_id: parseInt(scenicId), start_node_id: fromNode,
        destinations: multiDests, strategy, transport, return_to_start: returnToStart,
      })
      setMultiResult(res.data)
      if (res.data?.unreachable_names?.length) {
        message.warning(`部分节点不可达：${res.data.unreachable_names.join('、')}`)
      } else {
        message.success(`多点路线规划完成！总${strategy === 'distance' ? '距离' : '时间'}: ${res.data.total_cost} ${res.data.cost_unit}`)
      }
    } catch (e) { message.error(e.message || '路线规划失败') }
    setCalculating(false)
  }

  const resetAll = () => {
    setFromNode(null); setToNode(null); setMultiDests([]); setPathResult(null); setMultiResult(null)
  }

  const nodeMap = {}
  mapData.nodes.forEach(n => { nodeMap[n.id] = n })

  if (loading) return <Spin size="large" className="flex justify-center py-20" />

  return (
    <div>
      <Row gutter={16}>
        <Col xs={24} md={16}>
          <Card title="地图" size="small" className="mb-4">
            <canvas ref={canvasRef} onClick={handleCanvasClick}
                    style={{ width: '100%', height: 500, cursor: 'crosshair' }}
                    className="map-canvas" />
            {(mapData.nodes.length > MAX_RENDER_NODES || mapData.edges.length > MAX_RENDER_EDGES) && (
              <div className="mt-2 text-xs text-amber-600">
                地图数据较大，画布已自动简化显示；路径计算和节点选择仍基于完整数据。
              </div>
            )}
            <div className="text-xs text-gray-400 mt-2">
              <span className="inline-block w-3 h-3 rounded-full bg-green-500 mr-1" /> 起点
              <span className="inline-block w-3 h-3 rounded-full bg-red-500 ml-3 mr-1" /> 终点
              <span className="inline-block w-3 h-3 rounded-full bg-orange-400 ml-3 mr-1" /> 途经点
              <span className="inline-block w-3 h-3 rounded-full bg-blue-500 ml-3 mr-1" /> 普通节点
              <span className="text-blue-500 ml-3">--- 规划路径</span>
            </div>
            <div className="text-xs text-gray-400 mt-1">
              道路拥挤度：
              <span className="inline-block w-6 h-1 bg-green-500 ml-2 mr-1 align-middle" /> 畅通
              <span className="inline-block w-6 h-1 bg-yellow-500 ml-3 mr-1 align-middle" /> 较忙
              <span className="inline-block w-6 h-1 bg-red-500 ml-3 mr-1 align-middle" /> 拥挤
            </div>
          </Card>
        </Col>
        <Col xs={24} md={8}>
          <Card title="路线规划" size="small" className="mb-4">
            <Radio.Group value={planMode} onChange={(e) => { setPlanMode(e.target.value); resetAll() }} className="mb-3 w-full">
              <Radio.Button value="single" className="w-1/2 text-center">单点导航</Radio.Button>
              <Radio.Button value="multi" className="w-1/2 text-center">多点规划</Radio.Button>
            </Radio.Group>

            <div className="mb-3">
              <div className="text-sm font-semibold mb-1">策略</div>
              <Radio.Group value={strategy} onChange={(e) => setStrategy(e.target.value)} size="small">
                <Radio.Button value="distance">最短距离</Radio.Button>
                <Radio.Button value="time">最短时间</Radio.Button>
              </Radio.Group>
            </div>

            <div className="mb-3">
              <div className="text-sm font-semibold mb-1">交通工具</div>
              <Radio.Group value={transport} onChange={(e) => setTransport(e.target.value)} size="small">
                {transportOptions.map(t => (
                  <Radio.Button key={t.value} value={t.value}>{t.label}</Radio.Button>
                ))}
              </Radio.Group>
            </div>

            <Divider className="my-2" />

            <div className="mb-2">
              <strong>起点: </strong>
              {fromNode ? <Tag color="green">{nodeMap[fromNode]?.name || fromNode}</Tag> : <span className="text-gray-400">点击地图选择</span>}
            </div>

            {planMode === 'single' ? (
              <div className="mb-3">
                <strong>终点: </strong>
                {toNode ? <Tag color="red">{nodeMap[toNode]?.name || toNode}</Tag> : <span className="text-gray-400">点击地图选择</span>}
              </div>
            ) : (
              <div className="mb-3">
                <strong>途经点: </strong>
                {multiDests.length > 0 ? multiDests.map(d => (
                  <Tag key={d} color="orange" closable onClose={() => setMultiDests(multiDests.filter(x => x !== d))}>
                    {nodeMap[d]?.name || d}
                  </Tag>
                )) : <span className="text-gray-400">点击地图添加</span>}
                <div className="mt-2">
                  <Checkbox checked={returnToStart} onChange={(e) => setReturnToStart(e.target.checked)}>
                    返回起点
                  </Checkbox>
                </div>
              </div>
            )}

            <Space className="w-full">
              <Button type="primary" loading={calculating}
                      onClick={planMode === 'single' ? calcSingle : calcMulti}
                      icon={<CompassOutlined />}>
                开始规划
              </Button>
              <Button onClick={resetAll}>重置</Button>
            </Space>
          </Card>

          {/* 结果 */}
          {(pathResult || multiResult) && (
            <Card title="规划结果" size="small">
              {pathResult && (
                <div>
                  <p><strong>距离:</strong> {pathResult.distance}米</p>
                  <p><strong>预计时间:</strong> {pathResult.time}分钟</p>
                  <p><strong>平均拥挤度:</strong> <Tag color={pathResult.avg_congestion >= 0.75 ? 'red' : pathResult.avg_congestion >= 0.45 ? 'orange' : 'green'}>{congestionLabel(pathResult.avg_congestion)} {pathResult.avg_congestion}</Tag></p>
                  <p><strong>途经节点:</strong> {pathResult.node_count}个</p>
                  <Divider className="my-2" />
                  {pathResult.edge_details?.length > 0 && (
                    <div className="text-xs mb-2">
                      <div className="font-semibold mb-1">路段拥挤情况:</div>
                      {pathResult.edge_details.slice(0, 8).map((edge, i) => (
                        <Tag key={`${edge.from_node_id}-${edge.to_node_id}-${i}`} color={edge.congestion >= 0.75 ? 'red' : edge.congestion >= 0.45 ? 'orange' : 'green'}>
                          {edge.road_name || '道路'} {congestionLabel(edge.congestion)} {edge.congestion}
                        </Tag>
                      ))}
                      {pathResult.edge_details.length > 8 && <span className="text-gray-400">等 {pathResult.edge_details.length} 段</span>}
                    </div>
                  )}
                  <div className="text-xs">
                    {pathResult.path_details?.map((n, i) => (
                      <span key={i}>
                        {i > 0 && <span className="mx-1 text-blue-400">→</span>}
                        <Tag size="small">{n.name}</Tag>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {multiResult && (
                <div>
                  <p><strong>总{strategy === 'distance' ? '距离' : '时间'}:</strong> {multiResult.total_cost} {multiResult.cost_unit}</p>
                  <Divider className="my-2" />
                  <div className="text-sm font-semibold mb-1">访问顺序:</div>
                  <Steps direction="vertical" size="small" current={-1}
                    items={[
                      { title: nodeMap[fromNode]?.name || '起点', description: '出发' },
                      ...(multiResult.visit_order || []).map((d, i) => ({
                        title: nodeMap[d]?.name || d,
                        description: multiResult.segments?.[i] ? `${multiResult.segments[i].cost} ${multiResult.cost_unit}` : '',
                      })),
                      ...(returnToStart ? [{ title: nodeMap[fromNode]?.name || '起点', description: '返回' }] : []),
                    ]}
                  />
                </div>
              )}
            </Card>
          )}
        </Col>
      </Row>
    </div>
  )
}

export default RoutePlanPage
