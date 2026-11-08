import { http, setToken, getToken } from '@/utils/http'

export const api = {
  sendCode: (target, purpose, targetType = 'PHONE') =>
    http.post('/auth/codes', { target, purpose, target_type: targetType }),
  loginByCode: (phone, code) => http.post('/auth/login/code', { phone, code }),
  loginByWechat: (code) => http.post('/auth/wechat/miniapp', { code }),
  me: () => http.get('/me'),
  profile: () => http.get('/me/profile'),
  updateProfile: (data) => http.patch('/me/profile', data),
  options: (params) => http.get('/units/options', params),
  certify: (unitId) => http.post('/certifications', { unit_id: unitId }),
  createAppeal: (data) => http.post('/appeals', data),
  resolutions: (scope = 'public') => http.get('/resolutions', { scope }),
  resolution: (id) => http.get(`/resolutions/${id}`),
  vote: (id, choice) => http.post(`/resolutions/${id}/votes`, { choice }),
  polls: () => http.get('/polls'),
  poll: (id) => http.get(`/polls/${id}`),
  respond: (id, answers) => http.post(`/polls/${id}/response`, { answers }),
  pollResult: (id) => http.get(`/polls/${id}/result`),
  claimsMine: () => http.get('/claims/mine'),
  createClaim: (data) => http.post('/claims', data),
  tasks: () => http.get('/approval/tasks'),
  decide: (instanceId, action) => http.post(`/approval/instances/${instanceId}/decision`, { action }),
  reports: () => http.get('/ledger/reports')
}

export { setToken, getToken }
