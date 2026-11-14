// MOD-085 / IFC-284：不可逆操作的二次确认（取消 → false，页面不得发请求）；uni.showModal 不支持富文本，后果用换行拼接
export const CONFIRM_TEXTS = {
  removeResident: { title: '移除同住人', consequences: ['该用户在本房屋将不再是同住人', '其在其他房屋的身份不变'] },
  leaveUnit: { title: '退出同住人身份', consequences: ['你在本房屋将不再是同住人', '若无其他身份将回到游客'] }
}

export function confirmDanger(key, vars = {}) {
  const spec = CONFIRM_TEXTS[key]
  if (!spec) return Promise.reject(new Error(`未知的确认类型：${key}`))
  const lines = vars.name ? [`对象：${vars.name}`, ...spec.consequences] : spec.consequences
  return new Promise((resolve) => {
    uni.showModal({
      title: spec.title,
      content: lines.join('\n'),
      confirmText: '确认',
      cancelText: '取消',
      success: (res) => resolve(Boolean(res && res.confirm)),
      fail: () => resolve(false)
    })
  })
}
