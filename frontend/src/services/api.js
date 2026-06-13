/**
 * API请求封装
 */
import axios from 'axios'
import { message } from 'antd'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截器
api.interceptors.response.use(
  (res) => {
    const data = res.data
    if (data.code && data.code >= 400) {
      message.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message))
    }
    return data
  },
  (err) => {
    if (err.response?.status === 401) {
      message.warning('请先登录')
    } else {
      message.error(err.response?.data?.message || '网络错误')
    }
    return Promise.reject(err)
  }
)

// ===== 认证 =====
export const authAPI = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  logout: () => api.post('/auth/logout'),
  check: () => api.get('/auth/check'),
  getProfile: () => api.get('/auth/profile'),
  updateProfile: (data) => api.put('/auth/profile', data),
}

// ===== 景区/校园 =====
export const scenicAPI = {
  list: (params) => api.get('/scenic/list', { params }),
  recommend: (params) => api.get('/scenic/recommend', { params }),
  search: (params) => api.get('/scenic/search', { params }),
  detail: (id) => api.get(`/scenic/${id}`),
  categories: () => api.get('/scenic/categories'),
  types: () => api.get('/scenic/types'),
}

// ===== 路线规划 =====
export const routeAPI = {
  shortest: (data) => api.post('/route/shortest', data),
  multi: (data) => api.post('/route/multi', data),
  transportOptions: (params) => api.get('/route/transport-options', { params }),
  nodes: (params) => api.get('/route/nodes', { params }),
  edges: (params) => api.get('/route/edges', { params }),
  mapData: (params) => api.get('/route/map-data', { params }),
}

// ===== 场所查询 =====
export const facilityAPI = {
  nearby: (params) => api.get('/facility/nearby', { params }),
  search: (params) => api.get('/facility/search', { params }),
  types: () => api.get('/facility/types'),
  byCategory: (params) => api.get('/facility/by-category', { params }),
}

// ===== 旅游日记 =====
export const diaryAPI = {
  create: (data) => api.post('/diary/create', data),
  update: (id, data) => api.put(`/diary/update/${id}`, data),
  delete: (id) => api.delete(`/diary/delete/${id}`),
  detail: (id) => api.get(`/diary/${id}`),
  my: (params) => api.get('/diary/my', { params }),
  public: (params) => api.get('/diary/public', { params }),
  byDestination: (params) => api.get('/diary/by-destination', { params }),
  search: (params) => api.get('/diary/search', { params }),
  fulltextSearch: (params) => api.get('/diary/fulltext-search', { params }),
  comment: (id, data) => api.post(`/diary/${id}/comment`, data),
  uploadImage: (id, formData) => api.post(`/diary/${id}/upload-image`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  deleteImage: (id, imageId) => api.delete(`/diary/${id}/image/${imageId}`),
  generateAnimation: (id, data) => api.post(`/diary/${id}/generate-animation`, data),
}

// ===== 美食推荐 =====
export const foodAPI = {
  recommend: (params) => api.get('/food/recommend', { params }),
  search: (params) => api.get('/food/search', { params }),
  cuisines: () => api.get('/food/cuisines'),
  restaurant: (id) => api.get(`/food/restaurant/${id}`),
}

// ===== 室内导航 =====
export const navAPI = {
  indoorPath: (data) => api.post('/navigation/indoor/path', data),
  buildingInfo: (id) => api.get(`/navigation/indoor/building/${id}`),
  buildings: (params) => api.get('/navigation/indoor/buildings', { params }),
}

export default api
