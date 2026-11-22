// MOD-082 / IFC-279：内部值 → 中文显示（键集合与 miniprogram/utils/labels.js 一致，由测试守护）
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

// REQ-FUNC-158（DEF-020）：仅 Web 使用，命名不带 _LABELS 后缀，不纳入与小程序 labels.js 的键集合对齐检查
export const FLOW_SCOPE_TEXT = { RESOLUTION: '决议', EXPENSE: '财务（报销/备用金）', INCOME: '收入表' }
export const APPROVAL_MODE_TEXT = { DESIGNATED: '指定负责人审批', HALF_MAJORITY: '半数人员同意' }
export const INCOME_STATUS_TEXT = {
  DRAFT: '草稿', PENDING: '审批中', EFFECTIVE: '已生效', REJECTED: '未通过', WITHDRAWN: '已撤回', VOID: '已作废'
}

export function textOf(table, code) {
  return table[code] || code || ''
}
