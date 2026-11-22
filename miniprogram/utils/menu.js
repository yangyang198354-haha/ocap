// MOD-181 / IFC-400：小程序菜单文案与分组的唯一来源（与 Web C-363 逐字一致）。
export const MP_HOUSING_TABS = [
  { key: 'identity', label: '我的身份与房屋' },
  { key: 'appeal', label: '我的认证与申述' },
  { key: 'applications', label: '我的同住人申请' }
]

export const MP_USER_GROUPS = [
  {
    key: 'personal',
    label: '个人设置',
    items: [
      { key: 'profile', label: '个人资料', url: '/pages/profile-setup/index' },
      { key: 'phone', label: '绑定手机', url: '/pages/phone/index' },
      { key: 'email', label: '邮箱验证', url: '/pages/email/index' },
      { key: 'cancel', label: '账号注销', url: '/pages/cancel/index' }
    ]
  },
  {
    key: 'system',
    label: '系统设置',
    items: [
      { key: 'style', label: '界面风格', action: 'theme' }
    ]
  }
]
