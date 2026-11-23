// MOD-082 / IFC-279：不可逆操作的二次确认（取消/关闭 → false，页面不得发请求）
import { h } from 'vue'
import { ElMessageBox } from 'element-plus'

export const CONFIRM_TEXTS = {
  revokeMembership: { title: '撤销产权认证', consequences: ['该用户将失去该房屋的身份', '撤销户主认证会触发户主接任，其业委会席位可能随之失效'] },
  revokeSeat: { title: '撤销业委会席位', consequences: ['该用户将不再是业委会成员，无法再发起或审批相关事项'] },
  deleteUnit: { title: '删除专有部分', consequences: ['该专有部分及其业主、手机号登记将被删除', '已认证该房屋的用户将失去相应身份'] },
  deleteFlow: { title: '删除审批流程', consequences: ['流程配置将被永久删除', '已被审批记录使用的流程不能删除，只能停用'] },
  voidIncome: { title: '作废收入表', consequences: ['已生效的收入将从台账中作废', '此操作不可撤销'] },
  withdrawResolution: { title: '撤回决议', consequences: ['决议将退出审批，需修改后重新提交'] },
  withdrawClaim: { title: '撤回申请', consequences: ['申请将退出审批，需修改后重新提交'] },
  withdrawIncome: { title: '撤回收入表', consequences: ['收入表将退出审批，需修改后重新提交'] },
  removeResident: { title: '移除同住人', consequences: ['该用户在本房屋将不再是同住人', '其在其他房屋的身份不变'] },
  leaveUnit: { title: '退出同住人身份', consequences: ['你在本房屋将不再是同住人', '若无其他身份将回到游客'] },
  cancelAccount: {
    title: '注销账号',
    consequences: ['户主身份将由他人接任', '业委会席位失效', '待处理的申请与申诉被关闭', '账号不可恢复']
  }
}

export async function confirmDanger(key, vars = {}) {
  const spec = CONFIRM_TEXTS[key]
  if (!spec) throw new Error(`未知的确认类型：${key}`)
  const lines = vars.name ? [`对象：${vars.name}`, ...spec.consequences] : spec.consequences
  try {
    await ElMessageBox.confirm(h('div', lines.map((line) => h('p', line))), spec.title, {
      type: 'warning',
      confirmButtonText: '确认',
      cancelButtonText: '取消'
    })
    return true
  } catch (e) {
    return false
  }
}
