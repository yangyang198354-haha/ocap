// 回流 2（DEF-021/022 同类扫描）：管理端表格枚举原值的中文映射；独立成文件，不进入 labels.js 的登记集合（TC-UNIT-588）
export const CLAIM_TYPE_TEXT = { REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销' }
export const CLAIM_STATUS_TEXT = { PENDING: '审批中', APPROVED: '已通过', REJECTED: '未通过', WITHDRAWN: '已撤回' }
export const AUDIT_ACTOR_TEXT = { MEMBER: '成员', ADMIN: '管理员', SYSTEM: '系统' }
export const AUDIT_RESULT_TEXT = { SUCCESS: '成功', FAILURE: '失败', DENIED: '拒绝' }
