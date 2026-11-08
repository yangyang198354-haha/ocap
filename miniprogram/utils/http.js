const BASE = import.meta.env.VITE_API_BASE || '/api/v1'
export const TOKEN_KEY = 'ocap_token'

export function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) uni.setStorageSync(TOKEN_KEY, token)
  else uni.removeStorageSync(TOKEN_KEY)
}

function handleFailure(resp, reject) {
  if (resp.statusCode === 401) {
    setToken('')
    uni.reLaunch({ url: '/pages/login/index' })
  }
  const body = resp.data || {}
  const err = new Error(body.message || '请求失败')
  err.code = body.code || 'HTTP_ERROR'
  err.details = body.details || {}
  reject(err)
}

export function request(method, url, data) {
  return new Promise((resolve, reject) => {
    const header = { 'content-type': 'application/json' }
    const token = getToken()
    if (token) header.Authorization = `Bearer ${token}`
    uni.request({
      url: `${BASE}${url}`,
      method,
      data,
      header,
      success: (resp) => {
        if (resp.statusCode >= 200 && resp.statusCode < 300) {
          resolve(resp.data)
          return
        }
        handleFailure(resp, reject)
      },
      fail: (error) => reject(new Error(error.errMsg || '网络异常'))
    })
  })
}

// 上传附件：POST /attachments（multipart：file + purpose），返回 { id, name, size, content_type }
export function upload(filePath, purpose) {
  return new Promise((resolve, reject) => {
    const header = {}
    const token = getToken()
    if (token) header.Authorization = `Bearer ${token}`
    uni.uploadFile({
      url: `${BASE}/attachments`,
      filePath,
      name: 'file',
      formData: { purpose },
      header,
      success: (resp) => {
        let body = {}
        try {
          body = typeof resp.data === 'string' ? JSON.parse(resp.data) : resp.data || {}
        } catch (e) {
          body = {}
        }
        if (resp.statusCode >= 200 && resp.statusCode < 300) {
          resolve(body)
          return
        }
        handleFailure({ statusCode: resp.statusCode, data: body }, reject)
      },
      fail: (error) => reject(new Error(error.errMsg || '上传失败'))
    })
  })
}

export const http = {
  get: (url, data) => request('GET', url, data),
  post: (url, data) => request('POST', url, data),
  put: (url, data) => request('PUT', url, data),
  patch: (url, data) => request('PATCH', url, data),
  delete: (url, data) => request('DELETE', url, data)
}
