// 收入表模板下载（TC-UNIT-1603）：页面“下载模板”调用业委会成员接口并触发文件保存。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { mountPage, routeTable } from './helpers.js'
import Income from '@/portal/Income.vue'

const flush = async () => {
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await flushPromises()
}

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
  localStorage.setItem('ocap_token', 'tok')
  document.body.innerHTML = ''
  URL.createObjectURL = vi.fn(() => 'blob:mock')
  URL.revokeObjectURL = vi.fn()
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
})

describe('收入表模板下载（TC-UNIT-1603）', () => {
  it('点“下载模板”请求 xlsx 模板并触发下载', async () => {
    mocked.http.get.mockImplementation(routeTable({
      '/admin/income/sheets': { count: 0, results: [] },
      '/system/limits': {},
      '/approval/flows': { results: [] },
      '/admin/income/template': new Blob(['x'], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      })
    }))
    const { wrapper } = await mountPage(Income)
    await flush()

    const button = wrapper.findAll('button').find((b) => b.text().includes('下载模板'))
    expect(button).toBeTruthy()
    await button.trigger('click')
    await flush()

    expect(mocked.http.get).toHaveBeenCalledWith('/admin/income/template',
      { params: { file_type: 'xlsx' }, responseType: 'blob' })
    expect(URL.createObjectURL).toHaveBeenCalled()
    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled()
  })
})
