// MOD-085 / IFC-284：内部值 → 中文显示（键集合与 frontend/src/shared/labels.js 一致，由测试守护）
export const ROLE_LABELS = { HEAD: '户主', OWNER: '产权业主', RESIDENT: '同住人' }
export const POSITION_LABELS = { CHAIR: '主任', VICE_CHAIR: '副主任', MEMBER: '委员', REPRESENTATIVE: '业主代表' }
export const IDENTITY_LABELS = { ...POSITION_LABELS, ...ROLE_LABELS, GUEST: '游客' }
export const APPLICATION_STATUS_LABELS = {
  PENDING: '待审批', APPROVED: '已通过', REJECTED: '已拒绝', CLOSED: '已关闭（申请人已注销）', WITHDRAWN: '已撤回'
}
export const APPEAL_STATUS_LABELS = {
  PENDING: '待审核', APPROVED: '已通过', REJECTED: '已驳回', CLOSED: '已关闭（申请人已注销）', WITHDRAWN: '已撤回'
}
export const POLL_STATUS_LABELS = { OPEN: '进行中', CLOSED: '已结束' }
export const SEAT_STATUS_LABELS = {
  ACTIVE: '在任', REVOKED: '已撤销', EXPIRED: '已到期', INVALIDATED: '资格失效', REPLACED: '已变更', MERGED: '已合并'
}
export const ACCOUNT_STATUS_LABELS = { ACTIVE: '启用', DISABLED: '停用', CANCELLED: '已注销' }

const TABLES = {
  application: APPLICATION_STATUS_LABELS,
  appeal: APPEAL_STATUS_LABELS,
  poll: POLL_STATUS_LABELS,
  seat: SEAT_STATUS_LABELS,
  account: ACCOUNT_STATUS_LABELS
}

export function statusLabel(kind, code) {
  const table = TABLES[kind] || {}
  return table[code] || code || ''
}

export function yesNo(value) {
  if (value === null || value === undefined) return ''
  return value ? '是' : '否'
}

// 时间统一显示为“年-月-日 时:分”（Asia/Shanghai；后端返回已含 +08:00 偏移，直接取字面值）
export function formatDateTime(value) {
  if (!value) return ''
  return String(value).replace('T', ' ').slice(0, 16)
}

// MOD-191：三端一致的步骤与动作文案
export const STEP_STRATEGY_LABELS = { ANY: '或签（任一通过）', ALL: '会签（全部同意）' }
export const STEP_STATUS_LABELS = { PENDING: '未开始', ACTIVE: '进行中', APPROVED: '已通过', REJECTED: '已拒绝' }
export const APPROVAL_ACTION_LABELS = { SUBMIT: '提交', APPROVE: '通过', REJECT: '拒绝', WITHDRAW: '撤回' }
export const APPROVAL_STATUS_LABELS = { PENDING: '待审批', APPROVED: '通过', REJECTED: '拒绝', WITHDRAWN: '已撤回' }
