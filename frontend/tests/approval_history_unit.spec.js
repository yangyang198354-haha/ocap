// ocap_approval_history GROUP_D：历史记录 API 参数装配单元测试。
import { beforeEach, describe, expect, it, vi } from 'vitest'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import { approvalApi, unitApi } from '@/shared/api'

const { http } = mocked

beforeEach(() => {
  vi.clearAllMocks()
  for (const method of Object.values(http)) method.mockReset().mockResolvedValue({})
})

describe('审批历史 API 参数装配', () => {
  it('TC-UNIT-2301 / AC-371-01：approvalApi.tasks 透传 handled、scope 与分页参数', async () => {
    await approvalApi.tasks('RESOLUTION', { view: 'handled', page: 2, page_size: 20 })
    expect(http.get).toHaveBeenCalledWith('/approval/tasks', {
      params: { scope: 'RESOLUTION', view: 'handled', page: 2, page_size: 20 }
    })
  })

  it('TC-UNIT-2302 / AC-372-01：approvedResidentApplications 只发起固定路径 GET', async () => {
    await unitApi.approvedResidentApplications()
    expect(http.get).toHaveBeenCalledWith('/resident-applications/approved', { params: undefined })
    expect(http.post).not.toHaveBeenCalled()
  })
})
