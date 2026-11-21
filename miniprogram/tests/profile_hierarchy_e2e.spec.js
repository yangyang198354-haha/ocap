// ocap_profile_hierarchy GROUP_D：critical path 替代用例（小程序“我的”页多步旅程）。
import { describe, expect, it } from 'vitest'
import { mountPage, respondWith } from './helpers.js'
import Me from '../pages/me/index.vue'

const UNIT_A = {
  unit_id: 107, specific_part: '1栋1单元9层902号', role: 'HEAD', role_label: '产权业主',
  unit_type: 'RESIDENCE', unit_type_label: '住宅', area: '89.50', area_display: '89.50 ㎡'
}
const ME = (labels, units = []) => ({
  profile: { id: 1, nickname: '张三', phone: '138****0000' },
  identities: { is_guest: labels.includes('游客'), units, committee: null, labels }
})

describe('critical path（替代）：小程序“我的”页实名降级与恢复（US-276）', () => {
  it('TC-E2E-1503：实名请求失败时无徽章，恢复后显示实名与徽章', async () => {
    uni.request.mockImplementation(({ url, success }) => {
      const path = url.replace('/api/v1', '')
      if (path === '/me') return success({ statusCode: 200, data: ME(['产权业主'], [UNIT_A]) })
      if (path === '/me/profile') return success({ statusCode: 500, data: { code: 'SERVER_ERROR' } })
      return success({ statusCode: 200, data: { results: [] } })
    })
    const failed = await mountPage(Me)
    expect(failed.wrapper.find('.real-name').exists()).toBe(false)
    expect(failed.wrapper.text()).not.toContain('已实名认证')

    respondWith({
      'GET /me': ME(['产权业主'], [UNIT_A]),
      'GET /me/housing': { units: [UNIT_A] },
      'GET /me/profile': { real_name: '杨扬', real_name_visible: true },
      'GET /ledger/reports': { results: [] }
    })
    const recovered = await mountPage(Me)
    const text = recovered.wrapper.text()
    expect(text.indexOf('张三')).toBeLessThan(text.indexOf('杨扬'))
    expect(text.indexOf('杨扬')).toBeLessThan(text.indexOf('产权业主'))
    const badge = recovered.wrapper.findAll('.tag').find((t) => t.text().includes('已实名认证'))
    expect(badge).toBeTruthy()
  })
})
