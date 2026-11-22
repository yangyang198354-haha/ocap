// MOD-181 / IFC-400：小程序菜单文案与分组的唯一来源（与 Web C-363 逐字一致）。
export const MP_HOUSING_TABS = [
  { key: 'identity', label: '我的身份与房屋' },
  { key: 'appeal', label: '我的认证与申述' },
  { key: 'applications', label: '我的同住人申请' }
]

// “我的”页只保留两个入口；账号相关功能收敛到“个人资料”页内 Tab，界面风格收敛到“系统设置”页内 Tab。
export const MP_USER_ENTRIES = [
  { key: 'profile', label: '个人资料', url: '/pages/account/index' },
  { key: 'system', label: '系统设置', url: '/pages/settings/index' }
]

export const MP_ACCOUNT_TABS = [
  { key: 'profile', label: '个人资料' },
  { key: 'phone', label: '绑定手机' },
  { key: 'email', label: '邮箱验证' },
  { key: 'cancel', label: '账号注销' }
]

export const MP_SETTINGS_TABS = [
  { key: 'style', label: '界面风格' }
]
