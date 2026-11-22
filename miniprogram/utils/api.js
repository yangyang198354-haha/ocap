import { http, setToken, getToken, upload } from '@/utils/http'

export const api = {
  sendCode: (target, purpose, targetType = 'PHONE') =>
    http.post('/auth/codes', { target, purpose, target_type: targetType }),
  // client: 'miniapp'：所有小程序登录方式均为 7 天会话（IFC-268 / REQ-FUNC-147）
  loginByCode: (phone, code) => http.post('/auth/login/code', { phone, code, client: 'miniapp' }),
  // 密码登录：identifier 为账号或手机号（REQ-FUNC-003 / AC-003-02）
  loginByPassword: (identifier, password) =>
    http.post('/auth/login/password', { identifier, password, client: 'miniapp' }),
  loginByWechat: (code) => http.post('/auth/wechat/miniapp', { code }),
  me: () => http.get('/me'),
  // 我的房屋聚合（IFC-261）与当前规则限制（IFC-272）
  housing: () => http.get('/me/housing'),
  // 手机号匹配清册后的引导确认（IFC-332/333/334）：请求不带手机号与姓名，服务端按本人已验证手机号重算
  registryMatches: () => http.get('/me/registry-matches'),
  confirmRegistryMatches: (unitIds) => http.post('/me/registry-matches/confirm', { unit_ids: unitIds }),
  dismissRegistryMatches: () => http.post('/me/registry-matches/dismiss', {}),
  limits: () => http.get('/system/limits'),
  profile: () => http.get('/me/profile'),
  updateProfile: (data) => http.patch('/me/profile', data),
  // 界面风格偏好（IFC-142/143）
  theme: () => http.get('/me/theme'),
  setTheme: (theme) => http.put('/me/theme', { theme }),
  // 绑定/换绑手机号；遇到已属他人的手机号后端会合并账号，返回 { merged, token?, user? }
  sendMeCode: (purpose, target) => http.post('/me/codes', target ? { purpose, target } : { purpose }),
  // MOD-182 / IFC-401：邮箱验证与账号注销（复用后端既有接口）
  verifyEmail: (email, code) => http.post('/me/email/verify', { email, code }),
  cancelAccount: (phone, code) => http.post('/me/cancel', { phone, code }),
  bindPhone: (phone, code) => http.post('/me/phone/bind', { phone, code }),
  changePhone: (oldPhone, newPhone, oldCode, newCode) =>
    http.post('/me/phone/change', { old_phone: oldPhone, new_phone: newPhone, old_code: oldCode, new_code: newCode }),
  // 返回 { level, skipped, has_empty, options }；level=room 时每项含 label/unit_type_label/area（IFC-152）
  options: (params) => http.get('/units/options', params),
  certify: (unitId, name) => http.post('/certifications', { unit_id: unitId, name }),
  // data: { unit_id, owner_name, proof_ids: [附件 id 1~5 个] }，后端要求产权人名字与至少一份产权证明
  createAppeal: (data) => http.post('/appeals', data),
  myAppeals: () => http.get('/appeals/mine'),
  // 同住人链路（REQ-FUNC-142~145）
  createResidentApplication: (data) => http.post('/resident-applications', data),
  myResidentApplications: () => http.get('/resident-applications/mine'),
  residentApplicationsToReview: () => http.get('/resident-applications/to-review'),
  decideResidentApplication: (id, decision) => http.post(`/resident-applications/${id}/decision`, { decision }),
  removeResident: (unitId, userId) => http.delete(`/units/${unitId}/residents/${userId}`),
  leaveUnit: (unitId) => http.post(`/units/${unitId}/leave`, {}),
  upload,
  resolutions: (scope = 'public', params) => http.get('/resolutions', { scope, ...params }),
  resolution: (id) => http.get(`/resolutions/${id}`),
  vote: (id, choice) => http.post(`/resolutions/${id}/votes`, { choice }),
  polls: (params) => http.get('/polls', params),
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
  tasks: (params) => http.get('/approval/tasks', params),
  decide: (instanceId, action) => http.post(`/approval/instances/${instanceId}/decision`, { action }),
  reports: (params) => http.get('/ledger/reports', params),
  report: (id) => http.get(`/ledger/reports/${id}`),
  infoPosts: (params) => http.get('/info/posts', params),
  infoPost: (id) => http.get(`/info/posts/${id}`, { fmt: 'blocks' })
}

export { setToken, getToken }
