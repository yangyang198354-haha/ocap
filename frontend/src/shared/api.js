import { adminHttp, http } from './http'
import { IMPORT_REQUEST_TIMEOUT_MS } from '../admin/registryImport'

const get = (url, params) => http.get(url, { params })
const post = (url, data) => http.post(url, data)

export const authApi = {
  sendCode: (target, purpose, targetType = 'PHONE') =>
    post('/auth/codes', { target, purpose, target_type: targetType }),
  register: (phone, code) => post('/auth/register', { phone, code }),
  loginByCode: (phone, code, rememberMe) => post('/auth/login/code', { phone, code, remember_me: rememberMe }),
  loginByPassword: (identifier, password, rememberMe) =>
    post('/auth/login/password', { identifier, password, remember_me: rememberMe }),
  loginByEmail: (email, code, rememberMe) => post('/auth/login/email', { email, code, remember_me: rememberMe }),
  logout: () => post('/auth/logout', {}),
  wechatWebParams: () => get('/auth/wechat/web/params'),
  wechatExchange: (ticket) => post('/auth/wechat/web/exchange', { ticket })
}

export const meApi = {
  me: () => get('/me'),
  profile: () => get('/me/profile'),
  updateProfile: (data) => http.patch('/me/profile', data),
  // 界面风格偏好（IFC-142/143）：{ theme: string | null }
  theme: () => get('/me/theme'),
  setTheme: (theme) => http.put('/me/theme', { theme }),
  // data: { password, password_confirm, current_password? }，后端为 PUT
  setPassword: (data) => http.put('/me/password', data),
  sendCode: (purpose, target) => post('/me/codes', target ? { purpose, target } : { purpose }),
  verifyEmail: (code, email) => post('/me/email/verify', email ? { email, code } : { code }),
  // 绑定/换绑：后端遇到已属他人的手机号会合并账号，返回 { merged, token?, user? }（REQ-FUNC-026/028）
  bindPhone: (phone, code) => post('/me/phone/bind', { phone, code }),
  changePhone: (oldPhone, newPhone, oldCode, newCode) =>
    post('/me/phone/change', { old_phone: oldPhone, new_phone: newPhone, old_code: oldCode, new_code: newCode }),
  cancelAccount: (phone, code) => post('/me/cancel', { phone, code })
}

export const unitApi = {
  options: (params) => get('/units/options', params),
  certify: (unitId) => post('/certifications', { unit_id: unitId }),
  // data: { unit_id, proof_ids: [附件 id] }，后端要求至少一份产权证明
  createAppeal: (data) => post('/appeals', data),
  myAppeals: () => get('/appeals/mine'),
  createResidentApplication: (data) => post('/resident-applications', data),
  myResidentApplications: () => get('/resident-applications/mine'),
  residentApplicationsToReview: () => get('/resident-applications/to-review'),
  decideResidentApplication: (id, decision) => post(`/resident-applications/${id}/decision`, { decision }),
  removeResident: (unitId, userId) => http.delete(`/units/${unitId}/residents/${userId}`),
  leaveUnit: (unitId) => post(`/units/${unitId}/leave`, {})
}

export const approvalApi = {
  flows: (scope) => get('/approval/flows', scope ? { scope } : undefined),
  tasks: (scope) => get('/approval/tasks', scope ? { scope } : undefined),
  decide: (instanceId, action, comment) => post(`/approval/instances/${instanceId}/decision`, { action, comment })
}

export const resolutionApi = {
  list: (scope = 'public', params = {}) => get('/resolutions', { scope, ...params }),
  create: (data) => post('/resolutions', data),
  detail: (id) => get(`/resolutions/${id}`),
  withdraw: (id) => post(`/resolutions/${id}/withdraw`, {}),
  // 重新提交需带标题、正文、流程（半数同意另需 vote_deadline），后端 _validate_submission
  resubmit: (id, data) => post(`/resolutions/${id}/resubmit`, data),
  vote: (id, choice) => post(`/resolutions/${id}/votes`, { choice })
}

export const claimApi = {
  // 报销：{ amount, reason, occurred_on, invoice_ids, approval_flow_id }
  createReimbursement: (data) => post('/claims/reimbursements', data),
  // 备用金预借：{ amount, reason, expected_usage, expected_settle_on, approval_flow_id }
  createAdvance: (data) => post('/claims/advances', data),
  // 核销：{ advance_id, reimbursement_ids, reason, approval_flow_id }，差额为负即多退
  createSettlement: (data) => post('/claims/settlements', data),
  // scope=mine（我提交的）| todo（待我审批）；可带 type、status
  list: (params) => get('/claims', params),
  detail: (id) => get(`/claims/${id}`),
  withdraw: (id) => post(`/claims/${id}/withdraw`, {}),
  resubmit: (id, data) => post(`/claims/${id}/resubmit`, data)
}

export const incomeApi = {
  // 收入表的录入/提交类接口路径带 /admin 前缀，但权限为业委会成员（普通用户令牌）
  adminList: (params) => get('/admin/income/sheets', params),
  // 逐条录入：{ records: [{ occurred_on, amount, category, source_note, remark }], voucher_ids, title }
  create: (data) => post('/admin/income/sheets', data),
  importFile: (file) => {
    const body = new FormData()
    body.append('file', file)
    return http.post('/admin/income/sheets/import', body)
  },
  adminDetail: (id) => get(`/admin/income/sheets/${id}`),
  detail: (id) => get(`/income/sheets/${id}`),
  submit: (id, flowId) => post(`/admin/income/sheets/${id}/submit`, { approval_flow_id: flowId }),
  resubmit: (id, flowId) => post(`/admin/income/sheets/${id}/resubmit`, { approval_flow_id: flowId }),
  withdraw: (id) => post(`/admin/income/sheets/${id}/withdraw`, {}),
  voidSheet: (id) => post(`/admin/income/sheets/${id}/void`, {}),
  list: (params) => get('/income/sheets', params)
}

export const ledgerApi = {
  reports: (params) => get('/ledger/reports', params),
  reportDetail: (id) => get(`/ledger/reports/${id}`),
  // 手动生成限业委会成员（普通用户令牌）：{ period_type: QUARTER|YEAR, year, quarter? }
  generate: (data) => post('/ledger/reports/generate', data)
}

export const pollApi = {
  list: (params) => get('/polls', params),
  create: (data) => post('/polls', data),
  detail: (id) => get(`/polls/${id}`),
  // answers: [{ question_id, value }]；多选题 value 为选项数组
  respond: (id, answers) => post(`/polls/${id}/responses`, { answers }),
  result: (id) => get(`/polls/${id}/result`)
}

export const attachmentApi = {
  upload: (file, purpose) => {
    const body = new FormData()
    body.append('file', file)
    body.append('purpose', purpose)
    return http.post('/attachments', body)
  }
}

const admin = {
  login: (username, password) => adminHttp.post('/admin/auth/login', { username, password }),
  // 管理端风格偏好（IFC-251）：仅管理员令牌可读写
  theme: () => adminHttp.get('/admin/me/theme'),
  setTheme: (theme) => adminHttp.put('/admin/me/theme', { theme }),
  admins: () => adminHttp.get('/admin/admins'),
  createAdmin: (data) => adminHttp.post('/admin/admins', data),
  resetPassword: (id, password) => adminHttp.post(`/admin/admins/${id}/reset-password`, { password }),
  users: (params) => adminHttp.get('/admin/users', { params }),
  registryUnits: (params) => adminHttp.get('/admin/registry/units', { params }),
  createRegistryUnit: (data) => adminHttp.post('/admin/registry/units', data),
  updateRegistryUnit: (id, data) => adminHttp.patch(`/admin/registry/units/${id}`, data),
  deleteRegistryUnit: (id) => adminHttp.delete(`/admin/registry/units/${id}`),
  // owners: [{ id?, name, phones: [手机号] }]，全量替换（IFC-156）
  registryOwners: (id, owners) => adminHttp.put(`/admin/registry/units/${id}/owners`, { owners }),
  importRegistry: (file, dryRun) => {
    const body = new FormData()
    body.append('file', file)
    return adminHttp.post('/admin/registry/import', body, {
      params: dryRun ? { dry_run: 1 } : undefined,
      timeout: IMPORT_REQUEST_TIMEOUT_MS
    })
  },
  importTemplate: (fileType) =>
    adminHttp.get('/admin/registry/import/template', { params: { file_type: fileType }, responseType: 'blob' }),
  importSpec: () => adminHttp.get('/admin/registry/import/spec'),
  appeals: (params) => adminHttp.get('/admin/appeals', { params }),
  decideAppeal: (id, decision, rejectReason) =>
    adminHttp.post(`/admin/appeals/${id}/decision`, { decision, reject_reason: rejectReason }),
  memberships: (params) => adminHttp.get('/admin/memberships', { params }),
  revokeMembership: (userId, unitId) => adminHttp.post('/admin/memberships/revoke', { user_id: userId, unit_id: unitId }),
  seats: () => adminHttp.get('/admin/committee/seats'),
  createSeat: (data) => adminHttp.post('/admin/committee/seats', data),
  updateSeat: (id, data) => adminHttp.patch(`/admin/committee/seats/${id}`, data),
  deleteSeat: (id) => adminHttp.delete(`/admin/committee/seats/${id}`),
  committeeConfig: () => adminHttp.get('/admin/committee/config'),
  updateCommitteeConfig: (data) => adminHttp.put('/admin/committee/config', data),
  flows: (params) => adminHttp.get('/admin/approval/flows', { params }),
  createFlow: (data) => adminHttp.post('/admin/approval/flows', data),
  updateFlow: (id, data) => adminHttp.put(`/admin/approval/flows/${id}`, data),
  deleteFlow: (id) => adminHttp.delete(`/admin/approval/flows/${id}`),
  auditLogs: (params) => adminHttp.get('/admin/audit-logs', { params }),
  systemConfig: (key) => adminHttp.get(`/admin/system-config/${key}`),
  updateSystemConfig: (key, value) => adminHttp.put(`/admin/system-config/${key}`, { value }),
  downloadAttachment: (id) => adminHttp.get(`/attachments/${id}/download`, { responseType: 'blob' }),
  // 管理员令牌可读的财务数据：报销/备用金列表（/admin/claims）。收入表录入/生成报表属业委会成员权限，不在管理端
  claims: (params) => adminHttp.get('/admin/claims', { params }),

  // ---- 内容中心（IFC-190~231）----
  contentPosts: (params) => adminHttp.get('/admin/content/posts', { params }),
  createContentPost: (data) => adminHttp.post('/admin/content/posts', data),
  contentPost: (id) => adminHttp.get(`/admin/content/posts/${id}`),
  updateContentPost: (id, data) => adminHttp.patch(`/admin/content/posts/${id}`, data),
  publishContentPost: (id) => adminHttp.post(`/admin/content/posts/${id}/publish`, {}),
  offlineContentPost: (id) => adminHttp.post(`/admin/content/posts/${id}/offline`, {}),
  deleteContentPost: (id) => adminHttp.delete(`/admin/content/posts/${id}`),
  confirmContentText: (id) => adminHttp.post(`/admin/content/posts/${id}/confirm-text`, {}),
  previewContent: (data) => adminHttp.post('/admin/content/preview', data),
  styleTemplates: () => adminHttp.get('/admin/content/style-templates'),
  createStyleTemplate: (data) => adminHttp.post('/admin/content/style-templates', data),
  updateStyleTemplate: (id, data) => adminHttp.put(`/admin/content/style-templates/${id}`, data),
  deleteStyleTemplate: (id) => adminHttp.delete(`/admin/content/style-templates/${id}`),
  mediaList: (params) => adminHttp.get('/admin/content/media', { params }),
  uploadMedia: (file, title) => {
    const body = new FormData()
    body.append('file', file)
    if (title) body.append('title', title)
    return adminHttp.post('/admin/content/media', body)
  },
  renameMedia: (id, title) => adminHttp.patch(`/admin/content/media/${id}`, { title }),
  deleteMedia: (id) => adminHttp.delete(`/admin/content/media/${id}`),
  saveMedia: (id) => adminHttp.post(`/admin/content/media/${id}/save`, {}),
  contentServices: () => adminHttp.get('/admin/content/services'),
  saveContentService: (type, data) => adminHttp.put(`/admin/content/services/${type}`, data),
  testContentService: (type) => adminHttp.post(`/admin/content/services/${type}/test`, {}),
  llmOptions: () => adminHttp.get('/admin/content/llm/options'),
  promptTemplates: () => adminHttp.get('/admin/content/prompt-templates'),
  createPromptTemplate: (data) => adminHttp.post('/admin/content/prompt-templates', data),
  updatePromptTemplate: (id, data) => adminHttp.put(`/admin/content/prompt-templates/${id}`, data),
  deletePromptTemplate: (id) => adminHttp.delete(`/admin/content/prompt-templates/${id}`),
  aiText: (data) => adminHttp.post('/admin/content/ai/text', data),
  aiImage: (data) => adminHttp.post('/admin/content/ai/image', data),
  aiVideo: (data) => adminHttp.post('/admin/content/ai/video', data),
  contentJob: (id) => adminHttp.get(`/admin/content/jobs/${id}`),
  contentJobs: (params) => adminHttp.get('/admin/content/jobs', { params }),
  platformAccounts: () => adminHttp.get('/admin/content/platform-accounts'),
  createPlatformAccount: (data) => adminHttp.post('/admin/content/platform-accounts', data),
  updatePlatformAccount: (id, data) => adminHttp.patch(`/admin/content/platform-accounts/${id}`, data),
  deletePlatformAccount: (id) => adminHttp.delete(`/admin/content/platform-accounts/${id}`),
  pushDrafts: (postId, accountIds) => adminHttp.post(`/admin/content/posts/${postId}/drafts`, { account_ids: accountIds }),
  retryDraft: (pushId) => adminHttp.post(`/admin/content/drafts/${pushId}/retry`, {}),
  draftHistory: (postId, params) => adminHttp.get(`/admin/content/posts/${postId}/drafts/history`, { params }),
  exportPack: (postId, platform) =>
    adminHttp.get(`/admin/content/posts/${postId}/export-pack`, { params: { platform }, responseType: 'blob' }),
  copyPack: (postId, platform) => adminHttp.get(`/admin/content/posts/${postId}/copy`, { params: { platform } }),
  contentSettings: () => adminHttp.get('/admin/content/settings'),
  updateContentSettings: (values) => adminHttp.put('/admin/content/settings', { values })
}

export const infoApi = {
  list: (params) => http.get('/info/posts', { params }),
  detail: (id, fmt = 'html') => http.get(`/info/posts/${id}`, { params: { fmt } })
}

export { admin }
