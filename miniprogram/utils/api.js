import { http, setToken, getToken, upload } from '@/utils/http'

export const api = {
  sendCode: (target, purpose, targetType = 'PHONE') =>
    http.post('/auth/codes', { target, purpose, target_type: targetType }),
  loginByCode: (phone, code) => http.post('/auth/login/code', { phone, code }),
  // 密码登录：identifier 为账号或手机号（REQ-FUNC-003 / AC-003-02）
  loginByPassword: (identifier, password) => http.post('/auth/login/password', { identifier, password }),
  loginByWechat: (code) => http.post('/auth/wechat/miniapp', { code }),
  me: () => http.get('/me'),
  profile: () => http.get('/me/profile'),
  updateProfile: (data) => http.patch('/me/profile', data),
  // 绑定/换绑手机号；遇到已属他人的手机号后端会合并账号，返回 { merged, token?, user? }
  sendMeCode: (purpose, target) => http.post('/me/codes', target ? { purpose, target } : { purpose }),
  bindPhone: (phone, code) => http.post('/me/phone/bind', { phone, code }),
  changePhone: (oldPhone, newPhone, oldCode, newCode) =>
    http.post('/me/phone/change', { old_phone: oldPhone, new_phone: newPhone, old_code: oldCode, new_code: newCode }),
  options: (params) => http.get('/units/options', params),
  certify: (unitId) => http.post('/certifications', { unit_id: unitId }),
  // data: { unit_id, proof_ids: [附件 id] }，后端要求至少一份产权证明
  createAppeal: (data) => http.post('/appeals', data),
  upload,
  resolutions: (scope = 'public') => http.get('/resolutions', { scope }),
  resolution: (id) => http.get(`/resolutions/${id}`),
  vote: (id, choice) => http.post(`/resolutions/${id}/votes`, { choice }),
  polls: () => http.get('/polls'),
  poll: (id) => http.get(`/polls/${id}`),
  // answers: [{ question_id, value }]；多选题 value 为选项数组
  respond: (id, answers) => http.post(`/polls/${id}/responses`, { answers }),
  pollResult: (id) => http.get(`/polls/${id}/result`),
  // 报销 / 备用金 / 核销（与 Web 相同的后端接口）
  claims: (params) => http.get('/claims', params),
  flows: (scope) => http.get('/approval/flows', { scope }),
  createReimbursement: (data) => http.post('/claims/reimbursements', data),
  createAdvance: (data) => http.post('/claims/advances', data),
  createSettlement: (data) => http.post('/claims/settlements', data),
  withdrawClaim: (id) => http.post(`/claims/${id}/withdraw`, {}),
  tasks: () => http.get('/approval/tasks'),
  decide: (instanceId, action) => http.post(`/approval/instances/${instanceId}/decision`, { action }),
  reports: () => http.get('/ledger/reports')
}

export { setToken, getToken }
