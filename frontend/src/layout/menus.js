// MOD-120 / IFC-316、IFC-317：导航菜单配置与纯函数（宽屏侧栏、窄屏切换条、管理端抽屉共用）。
// 约定：key 在全菜单内唯一；默认（首个）二级分区沿用旧路径；'/' 仅精确匹配。

export const PORTAL_MENU = [
  { key: 'home', label: '主页', audience: 'all', match: ['/'], to: '/' },
  {
    key: 'units', label: '我的房屋', audience: 'all', match: ['/units', '/me/identity'],
    children: [
      // /me/identity 与 /units 同页（ADR-132）；待审批卡片并入该页底部，角标随之挂在此项（ADR-133）
      { key: 'units.identity', label: '我的身份与房屋', to: '/units', activeOn: ['/me/identity'], badge: 'pendingReview' },
      { key: 'units.pick', label: '认证产权', to: '/units/pick' },
      { key: 'units.appeal', label: '认证申诉', to: '/units/appeal' },
      { key: 'units.applications', label: '我的同住人申请', to: '/units/applications' },
      { key: 'units.appeals', label: '我的申诉', to: '/units/appeals' }
    ]
  },
  {
    key: 'resolutions', label: '决议', audience: 'all', match: ['/resolutions'],
    children: [
      { key: 'resolutions.public', label: '公开决议', to: '/resolutions' },
      { key: 'resolutions.mine', label: '我发起的', to: '/resolutions/mine' },
      { key: 'resolutions.todo', label: '待我表决', to: '/resolutions/todo' }
    ]
  },
  { key: 'polls', label: '投票/调查', audience: 'all', match: ['/polls'], to: '/polls' },
  {
    key: 'claims', label: '报销/备用金', audience: 'committee', match: ['/claims'],
    children: [
      { key: 'claims.mine', label: '我提交的', to: '/claims' },
      { key: 'claims.todo', label: '待我审批', to: '/claims/todo' }
    ]
  },
  { key: 'income', label: '收入表', audience: 'committee', match: ['/income'], to: '/income' },
  { key: 'reports', label: '财务报表', audience: 'all', match: ['/reports'], to: '/reports' },
  { key: 'tasks', label: '待办', audience: 'committee', match: ['/tasks'], to: '/tasks' },
  { key: 'info', label: '信息公开', audience: 'all', match: ['/info'], to: '/info' }
]

export const PORTAL_USER_MENU = [
  { key: 'me.style', label: '界面风格', to: '/me/style' },
  { key: 'me.identity', label: '我的身份与房屋', to: '/me/identity' },
  { key: 'me.profile', label: '个人资料', to: '/me/profile' },
  { key: 'me.phone', label: '手机号', to: '/me/phone' },
  { key: 'me.password', label: '设置密码', to: '/me/password' },
  { key: 'me.email', label: '邮箱验证', to: '/me/email' },
  { key: 'me.cancel', label: '账号注销', to: '/me/cancel' }
]

export const ADMIN_MENU = [
  { key: 'registry', label: '业主清册', audience: 'all', match: ['/admin/registry'], to: '/admin/registry' },
  { key: 'appeals', label: '申诉', audience: 'all', match: ['/admin/appeals'], to: '/admin/appeals' },
  { key: 'memberships', label: '房屋关系', audience: 'all', match: ['/admin/memberships'], to: '/admin/memberships' },
  { key: 'seats', label: '业委会席位', audience: 'all', match: ['/admin/seats'], to: '/admin/seats' },
  { key: 'flows', label: '审批流程', audience: 'all', match: ['/admin/flows'], to: '/admin/flows' },
  {
    key: 'finance', label: '财务', audience: 'all', match: ['/admin/finance'],
    children: [
      { key: 'finance.claims', label: '报销/备用金记录', to: '/admin/finance' },
      { key: 'finance.limit', label: '金额上限', to: '/admin/finance/limit' }
    ]
  },
  {
    key: 'users', label: '账号', audience: 'all', match: ['/admin/users'],
    children: [
      { key: 'users.admins', label: '管理员账号', to: '/admin/users' },
      { key: 'users.registered', label: '注册用户', to: '/admin/users/registered' }
    ]
  },
  {
    key: 'content', label: '内容管理', audience: 'all', match: ['/admin/content'],
    children: [
      { key: 'content.posts', label: '信息公开', to: '/admin/content/posts', activeOn: ['/admin/content/posts'] },
      { key: 'content.styles', label: '版式模板', to: '/admin/content/styles' },
      { key: 'content.media', label: '素材库', to: '/admin/content/media' },
      { key: 'content.models', label: 'AI 服务·模型与生成服务', to: '/admin/content/services' },
      { key: 'content.prompts', label: 'AI 服务·提示词模板', to: '/admin/content/services/prompts' },
      { key: 'content.platforms', label: '平台账户', to: '/admin/content/platforms' },
      { key: 'content.settings', label: '内容参数', to: '/admin/content/settings' }
    ]
  },
  {
    key: 'audit', label: '审计/配置', audience: 'all', match: ['/admin/audit'],
    children: [
      { key: 'audit.config', label: '系统配置', to: '/admin/audit' },
      { key: 'audit.logs', label: '审计日志', to: '/admin/audit/logs' }
    ]
  }
]

// 旧地址兼容（REQ-FUNC-215）：/units#appeal → /units/appeal；/units#review 本身即目的地（身份页底部卡片，ADR-133）
export const LEGACY_UNITS_HASH = { '#appeal': '/units/appeal' }

export function isPathMatch(path, pattern) {
  if (typeof path !== 'string' || typeof pattern !== 'string') return false
  if (pattern === '/') return path === '/'
  return path === pattern || path.startsWith(`${pattern}/`)
}

// auth.me 未加载时 isCommittee 为 false，先显示全员项（AC-211-04）；不置灰
export function visibleMenu(menu, ctx) {
  const isCommittee = Boolean(ctx?.isCommittee)
  return (menu || []).filter((node) => node.audience !== 'committee' || isCommittee)
}

export function resolveActive(menu, path) {
  const none = { node: null, leaf: null }
  if (typeof path !== 'string' || !path) return none
  const node = (menu || []).find((item) => item.match.some((pattern) => isPathMatch(path, pattern)))
  if (!node) return none
  const children = node.children || []
  const leaf = children.find((item) => item.to === path) ||
    children.find((item) => (item.activeOn || []).some((pattern) => isPathMatch(path, pattern))) ||
    null
  return { node, leaf }
}

export function nextOpenKey(menu, path) {
  const { node } = resolveActive(menu, path)
  return node && node.children ? node.key : null
}
