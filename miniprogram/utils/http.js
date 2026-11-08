const BASE = import.meta.env.VITE_API_BASE || '/api/v1'
export const TOKEN_KEY = 'ocap_token'

export function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) uni.setStorageSync(TOKEN_KEY, token)
  else uni.removeStorageSync(TOKEN_KEY)
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
        if (resp.statusCode === 401) {
          setToken('')
          uni.reLaunch({ url: '/pages/login/index' })
        }
        const body = resp.data || {}
        const err = new Error(body.message || '请求失败')
        err.code = body.code || 'HTTP_ERROR'
        err.details = body.details || {}
        reject(err)
      },
      fail: (error) => reject(new Error(error.errMsg || '网络异常'))
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
