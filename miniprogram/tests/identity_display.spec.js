// TC-MP-501~503：小程序身份与认证房屋展示（US-145/146/148 / AC-146-01~08、AC-148-01/02）
import { describe, expect, it } from 'vitest'
import { mountPage, respondWith } from './helpers.js'
import Index from '../pages/index/index.vue'
import Me from '../pages/me/index.vue'

const UNIT_A = {
  unit_id: 107, specific_part: '1栋1单元9层902号', role: 'HEAD', role_label: '产权业主',
  unit_type: 'RESIDENCE', unit_type_label: '住宅', area: '89.50', area_display: '89.50 ㎡'
}
const UNIT_B = {
  unit_id: 108, specific_part: '2栋1单元3层301号', role: 'RESIDENT', role_label: '同住人',
  unit_type: 'APARTMENT', unit_type_label: '公寓', area: null, area_display: '未登记'
}

const ME = (labels, units = []) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: labels.includes('游客'), units, committee: null, labels }
})

describe('小程序认证房屋（US-146 / US-148）', () => {
  // 改写（ocap_identity_property GR-C-001-a，AC-242-01）：小程序首页不再逐套显示名称/类型/面积/关系，只保留数量并可点击进入"我的房屋"；
  // 明细断言迁至"我的房屋"页（identity_property_pages.spec.js TC-MP-901）。
  it('TC-MP-501 首页只显示认证房屋数量（可点击进入我的房屋），不再逐套显示名称、类型、面积', async () => {
    respondWith({
      'GET /me': ME(['产权业主'], [UNIT_A, UNIT_B]),
      'GET /approval/tasks': { results: [] },
      'GET /resolutions': { results: [] },
      'GET /polls': { results: [] }
    })
    const { wrapper } = await mountPage(Index)
    const text = wrapper.text()
    expect(text).toContain('身份：产权业主')
    // 旧断言：含 902/301 号、住宅、89.50 ㎡、同住人、未登记 → 新断言：只有"共 2 套"，明细全部不在首页
    expect(text).toContain('共 2 套')
    for (const detail of ['1栋1单元9层902号', '2栋1单元3层301号', '89.50 ㎡', '住宅', '公寓', '未登记']) expect(text).not.toContain(detail)
    const card = wrapper.findAll('.card').find((c) => c.text().includes('点击查看明细'))
    await card.trigger('click')
    expect(uni.navigateTo).toHaveBeenCalledWith({ url: '/pages/units/index' })
  })

  it('TC-MP-502 游客：数量 0 与空状态', async () => {
    respondWith({
      'GET /me': ME(['游客']),
      'GET /approval/tasks': { results: [] },
      'GET /resolutions': { results: [] },
      'GET /polls': { results: [] }
    })
    const { wrapper } = await mountPage(Index)
    const text = wrapper.text()
    expect(text).toContain('身份：游客')
    expect(text).toContain('共 0 套')
    expect(text).toContain('暂无已认证房屋')
  })

  it('TC-MP-503 “我的”页显示单一身份，不出现“户主”', async () => {
    respondWith({
      'GET /me': ME(['产权业主'], [UNIT_A]),
      'GET /ledger/reports': { results: [] }
    })
    const { wrapper } = await mountPage(Me)
    const text = wrapper.text()
    expect(text).toContain('身份：产权业主')
    expect(text).not.toContain('户主')
  })
})
