import { adminHttp, http } from './http'

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
  setPassword: (data) => post('/me/password', data),
  sendCode: (purpose, target) => post('/me/codes', { purpose, target }),
  verifyEmail: (code) => post('/me/email/verify', { code }),
  bindPhone: (phone, code) => post('/me/phone/bind', { phone, code }),
  changePhone: (phone, code) => post('/me/phone/change', { phone, code }),
  cancelAccount: (code) => post('/me/cancel', { code })
}

export const unitApi = {
  options: (params) => get('/units/options', params),
  certify: (unitId) => post('/certifications', { unit_id: unitId }),
  createAppeal: (data) => post('/appeals', data),
  myAppeals: () => get('/appeals/mine'),
  createResidentApplication: (data) => post('/resident-applications', data),
  myResidentApplications: () => get('/resident-applications/mine'),
  residentApplicationsToReview: () => get('/resident-applications/to-review'),
  decideResidentApplication: (id, action) => post(`/resident-applications/${id}/decision`, { action }),
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
  resubmit: (id, flowId) => post(`/resolutions/${id}/resubmit`, { approval_flow_id: flowId }),
  vote: (id, choice) => post(`/resolutions/${id}/votes`, { choice })
}

export const claimApi = {
  create: (data) => post('/claims', data),
  mine: (params) => get('/claims/mine', params),
  detail: (id) => get(`/claims/${id}`),
  withdraw: (id) => post(`/claims/${id}/withdraw`, {}),
  resubmit: (id, flowId) => post(`/claims/${id}/resubmit`, { approval_flow_id: flowId }),
  settlement: (data) => post('/settlements', data),
  adminList: (params) => get('/admin/claims', params)
}

export const incomeApi = {
  adminList: (params) => get('/admin/income/sheets', params),
  importFile: (file) => {
    const body = new FormData()
    body.append('file', file)
    return http.post('/admin/income/sheets/import', body)
  },
  detail: (id) => get(`/income/sheets/${id}`),
  submit: (id, flowId) => post(`/admin/income/sheets/${id}/submit`, { approval_flow_id: flowId }),
  resubmit: (id, flowId) => post(`/admin/income/sheets/${id}/resubmit`, { approval_flow_id: flowId }),
  withdraw: (id) => post(`/admin/income/sheets/${id}/withdraw`, {}),
  voidSheet: (id) => post(`/admin/income/sheets/${id}/void`, {}),
  list: (params) => get('/income/sheets', params)
}

export const ledgerApi = {
  reports: (params) => get('/ledger/reports', params),
  reportDetail: (id) => get(`/ledger/reports/${id}`)
}

export const pollApi = {
  list: (params) => get('/polls', params),
  create: (data) => post('/polls', data),
  detail: (id) => get(`/polls/${id}`),
  respond: (id, answers) => post(`/polls/${id}/response`, { answers }),
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
  admins: () => adminHttp.get('/admin/admins'),
  createAdmin: (data) => adminHttp.post('/admin/admins', data),
  resetPassword: (id, password) => adminHttp.post(`/admin/admins/${id}/reset-password`, { password }),
  users: (params) => adminHttp.get('/admin/users', { params }),
  registryUnits: (params) => adminHttp.get('/admin/registry/units', { params }),
  createRegistryUnit: (data) => adminHttp.post('/admin/registry/units', data),
  updateRegistryUnit: (id, data) => adminHttp.patch(`/admin/registry/units/${id}`, data),
  deleteRegistryUnit: (id) => adminHttp.delete(`/admin/registry/units/${id}`),
  registryUnit: (id) => adminHttp.get(`/admin/registry/units/${id}`),
  registryUnitPhones: (id, phones) => adminHttp.put(`/admin/registry/units/${id}/phones`, { phones }),
  importRegistry: (file) => {
    const body = new FormData()
    body.append('file', file)
    return adminHttp.post('/admin/registry/import', body)
  },
  appeals: (params) => adminHttp.get('/admin/appeals', { params }),
  decideAppeal: (id, action, reason) => adminHttp.post(`/admin/appeals/${id}/decision`, { action, reason }),
  memberships: (params) => adminHttp.get('/admin/memberships', { params }),
  revokeMembership: (id) => adminHttp.post(`/admin/memberships/${id}/revoke`, {}),
  mergeUsers: (primaryId, secondaryId) => adminHttp.post('/admin/users/merge', { primary_id: primaryId, secondary_id: secondaryId }),
  seats: () => adminHttp.get('/admin/committee/seats'),
  createSeat: (data) => adminHttp.post('/admin/committee/seats', data),
  updateSeat: (id, data) => adminHttp.patch(`/admin/committee/seats/${id}`, data),
  deleteSeat: (id) => adminHttp.delete(`/admin/committee/seats/${id}`),
  committeeConfig: () => adminHttp.get('/admin/committee/config'),
  updateCommitteeConfig: (data) => adminHttp.put('/admin/committee/config', data),
  flows: (params) => adminHttp.get('/admin/approval/flows', { params }),
  createFlow: (data) => adminHttp.post('/admin/approval/flows', data),
  updateFlow: (id, data) => adminHttp.patch(`/admin/approval/flows/${id}`, data),
  deleteFlow: (id) => adminHttp.delete(`/admin/approval/flows/${id}`),
  auditLogs: (params) => adminHttp.get('/admin/audit-logs', { params }),
  systemConfig: (key) => adminHttp.get(`/admin/system-config/${key}`),
  updateSystemConfig: (key, value) => adminHttp.put(`/admin/system-config/${key}`, { value }),
  incomeSheets: (params) => adminHttp.get('/admin/income/sheets', { params }),
  claims: (params) => adminHttp.get('/admin/claims', { params }),
  createReport: (period) => adminHttp.post('/admin/ledger/reports', { period })
}

export { admin }
