/**
 * 日记详情页 - 查看日记、评论、评分
 */
import React, { useState, useEffect, useContext } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Alert, Card, Tag, Rate, Button, Divider, Input, List, Avatar, Spin, Empty, Space, message, Statistic, Row, Col, Modal, Image, Select, InputNumber } from 'antd'
import { UserOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MessageOutlined, CompressOutlined, VideoCameraOutlined } from '@ant-design/icons'
import { diaryAPI } from '../services/api'
import { UserContext } from '../App'

const { TextArea } = Input

const DEFAULT_ANIMATION_PROMPT = 'Create a 5-second cinematic yet realistic travel video based on the uploaded photo. Keep the main landmark, architecture, layout, colors, and perspective consistent with the original image. Use a slow and stable camera movement, such as a gentle forward dolly or subtle parallax, to make the scene feel alive. Add natural lighting, soft atmospheric motion, and a small amount of realistic pedestrian movement if appropriate. Do not change the identity or structure of the landmark. Do not add text, subtitles, logos, watermarks, fantasy effects, distorted faces, extra limbs, warped buildings, or unrealistic objects. The video should look clean, natural, high-quality, and suitable for a travel diary presentation.'
const VIDEO_SIZE_MAP = {
    landscape: { '480p': '832*480', '720p': '1280*704' },
    portrait: { '480p': '480*832', '720p': '704*1280' },
}

function DiaryDetailPage() {
    const { id } = useParams()
    const { user } = useContext(UserContext)
    const [diary, setDiary] = useState(null)
    const [loading, setLoading] = useState(true)
    const [commentContent, setCommentContent] = useState('')
    const [commentRating, setCommentRating] = useState(5)
    const [submitting, setSubmitting] = useState(false)
    const [generating, setGenerating] = useState(false)
    const [animationResult, setAnimationResult] = useState(null)
    const [animationModalOpen, setAnimationModalOpen] = useState(false)
    const [animationPrompt, setAnimationPrompt] = useState(DEFAULT_ANIMATION_PROMPT)
    const [animationImageId, setAnimationImageId] = useState(null)
    const [animationOrientation, setAnimationOrientation] = useState('landscape')
    const [animationResolution, setAnimationResolution] = useState('480p')
    const [animationSteps, setAnimationSteps] = useState(50)
    const [animationDuration, setAnimationDuration] = useState(5)
    const [animationSeed, setAnimationSeed] = useState(-1)
    const navigate = useNavigate()

    const fetchDiary = () => {
        diaryAPI.detail(id)
            .then((res) => setDiary(res.data))
            .catch(() => { })
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

    const handleGenerateAnimation = async () => {
        if (!user) { message.warning('请先登录'); return }
        if (!isOwner) { message.warning('只能为自己的日记生成动画'); return }
        if (!diary.images?.length) { message.warning('请先上传日记图片'); return }
        setGenerating(true)
        try {
            const res = await diaryAPI.generateAnimation(id, {
                prompt: animationPrompt,
                image_id: animationImageId || diary.images[0].id,
                size: VIDEO_SIZE_MAP[animationOrientation][animationResolution],
                sample_steps: animationSteps,
                frame_num: animationDuration * 24 + 1,
                seed: animationSeed,
            })
            setAnimationResult(res.data)
            setAnimationModalOpen(false)
            fetchDiary()
            message.success('动画生成成功')
        } catch (e) { /* ignore */ }
        setGenerating(false)
    }

    const openAnimationModal = () => {
        if (!diary.images?.length) { message.warning('请先上传日记图片'); return }
        setAnimationPrompt(DEFAULT_ANIMATION_PROMPT)
        setAnimationImageId(diary.images[0].id)
        setAnimationOrientation('landscape')
        setAnimationResolution('480p')
        setAnimationSteps(50)
        setAnimationDuration(5)
        setAnimationSeed(-1)
        setAnimationModalOpen(true)
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
                            <Button icon={<VideoCameraOutlined />} onClick={openAnimationModal}>生成旅游动画</Button>
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

                {(animationResult || diary.videos?.length > 0) && (
                    <>
                        <Divider>AIGC旅游动画</Divider>
                        {animationResult?.video_url && (
                            <Card size="small" className="mb-4" title="刚生成的视频">
                                <video src={animationResult.video_url} controls className="w-full rounded bg-black mb-3" />
                                <div className="text-gray-500 text-sm" style={{ whiteSpace: 'pre-wrap' }}>
                                    {animationResult.prompt}
                                </div>
                                {animationResult.params && (
                                    <div className="text-gray-400 text-xs mt-2">
                                        参数：{animationResult.params.size} · steps {animationResult.params.sample_steps} · frames {animationResult.params.frame_num} · seed {animationResult.params.seed}
                                    </div>
                                )}
                            </Card>
                        )}
                        {diary.videos?.length > 0 && (
                            <div className="grid grid-cols-1 gap-4 mb-6">
                                {diary.videos.map((video) => (
                                    <Card key={video.filename} size="small" title={video.filename}>
                                        <video src={video.video_url} controls className="w-full rounded bg-black" />
                                    </Card>
                                ))}
                            </div>
                        )}
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

            <Modal
                title="生成旅游动画"
                open={animationModalOpen}
                onCancel={() => setAnimationModalOpen(false)}
                onOk={handleGenerateAnimation}
                confirmLoading={generating}
                okText="开始生成"
                cancelText="取消"
                width={720}
            >
                <div className="mb-3 text-sm text-gray-500">用于生成的照片</div>
                <div className="grid grid-cols-4 gap-3 mb-4">
                    {(diary.images || []).map((img) => (
                        <button
                            type="button"
                            key={img.id}
                            className={`border rounded overflow-hidden bg-gray-100 ${animationImageId === img.id ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'}`}
                            onClick={() => setAnimationImageId(img.id)}
                        >
                            <img src={img.image_path} alt={img.description || '候选图片'} className="w-full h-20 object-cover" />
                        </button>
                    ))}
                </div>
                {diary.images?.find((img) => img.id === animationImageId) && (
                    <Image
                        src={diary.images.find((img) => img.id === animationImageId).image_path}
                        alt="用于生成的照片"
                        className="rounded object-cover"
                        style={{ width: '100%', maxHeight: 260 }}
                    />
                )}
                <Row gutter={12} className="mt-4">
                    <Col span={6}>
                        <div className="mb-1 text-sm text-gray-500">画面方向</div>
                        <Select
                            className="w-full"
                            value={animationOrientation}
                            onChange={setAnimationOrientation}
                            options={[
                                { value: 'landscape', label: '横屏' },
                                { value: 'portrait', label: '竖屏' },
                            ]}
                        />
                    </Col>
                    <Col span={6}>
                        <div className="mb-1 text-sm text-gray-500">分辨率</div>
                        <Select
                            className="w-full"
                            value={animationResolution}
                            onChange={setAnimationResolution}
                            options={[
                                { value: '480p', label: `480p (${VIDEO_SIZE_MAP[animationOrientation]['480p']})` },
                                { value: '720p', label: `720p (${VIDEO_SIZE_MAP[animationOrientation]['720p']})` },
                            ]}
                        />
                    </Col>
                    <Col span={6}>
                        <div className="mb-1 text-sm text-gray-500">时长</div>
                        <InputNumber
                            className="w-full"
                            min={1}
                            max={10}
                            value={animationDuration}
                            addonAfter="秒"
                            onChange={(v) => setAnimationDuration(v ?? 5)}
                        />
                    </Col>
                    <Col span={6}>
                        <div className="mb-1 text-sm text-gray-500">Seed</div>
                        <InputNumber className="w-full" value={animationSeed} onChange={(v) => setAnimationSeed(v ?? -1)} />
                    </Col>
                </Row>
                <Row gutter={12} className="mt-3">
                    <Col span={6}>
                        <div className="mb-1 text-sm text-gray-500">采样步数</div>
                        <InputNumber className="w-full" min={1} max={100} value={animationSteps} onChange={(v) => setAnimationSteps(v ?? 50)} />
                    </Col>
                    <Col span={18}>
                        <div className="mt-6 text-sm text-gray-500">
                            帧数按 24fps 自动计算：24 × {animationDuration} + 1 = {animationDuration * 24 + 1}
                        </div>
                    </Col>
                </Row>
                <div className="mt-4 mb-2 text-sm text-gray-500">提示词</div>
                <TextArea
                    rows={6}
                    value={animationPrompt}
                    onChange={(e) => setAnimationPrompt(e.target.value)}
                />
            </Modal>
        </div>
    )
}

export default DiaryDetailPage
