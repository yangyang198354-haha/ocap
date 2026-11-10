// MOD-036 / US-100：清册导入前端辅助函数（超时文案、结果摘要、错误清单 CSV）
import { describe, expect, it, vi, afterEach } from 'vitest'
import {
  IMPORT_REQUEST_TIMEOUT_MS,
  errorsCsv,
  formatImportResult,
  importErrorMessage,
  downloadText,
} from '@/admin/registryImport'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('registryImport helpers', () => {
  it('TC-UNIT-111 / AC-100-05：结果摘要为文字，不出现 JSON 原文', () => {
    const text = formatImportResult({
      rows_total: 100,
      imported: 98,
      updated: 2,
      owners_created: 120,
      failed: 0,
    })
    expect(text).toBe('共 100 行：新增 98 个专有部分、更新 2 个、业主 120 位，失败 0 行')
    expect(text).not.toContain('{')
    expect(formatImportResult(null)).toBe('')
  })

  it('TC-UNIT-112 / AC-100-07：超时错误给出缩小文件的重试建议', () => {
    expect(IMPORT_REQUEST_TIMEOUT_MS).toBe(100000)
    expect(importErrorMessage({ code: 'ECONNABORTED' })).toBe('导入超时，请缩小文件后重试')
    expect(importErrorMessage({ code: 'ETIMEDOUT' })).toBe('导入超时，请缩小文件后重试')
    expect(importErrorMessage({ message: '文件行数超过 20000' })).toBe('文件行数超过 20000')
  })

  it('TC-UNIT-113 / AC-100-02：错误清单导出为带表头的 CSV 并转义引号', () => {
    const text = errorsCsv([
      { row: 7, field: '手机号', reason: '手机号格式不正确' },
      { row: 15, field: null, reason: '车位须填"面积"' },
    ])
    const lines = text.split('\r\n')
    expect(lines[0]).toBe('"行号","字段","原因"')
    expect(lines[1]).toBe('"7","手机号","手机号格式不正确"')
    expect(lines[2]).toBe('"15","","车位须填""面积"""')
    expect(errorsCsv().split('\r\n')).toEqual(['"行号","字段","原因"'])
  })
})

describe('downloadText', () => {
  it('TC-UNIT-114 / AC-100-02：CSV 下载带 BOM 并使用文件名', () => {
    const click = vi.fn()
    const createElement = vi.spyOn(document, 'createElement')
    createElement.mockReturnValue({ set href(value) {}, set download(value) { this.name = value }, click })
    const createObjectURL = vi.fn(() => 'blob:mock')
    const revokeObjectURL = vi.fn()
    global.URL.createObjectURL = createObjectURL
    global.URL.revokeObjectURL = revokeObjectURL
    // DEF-012：revokeObjectURL 延迟 1 s 释放，用 fake timers 推进后断言，最后恢复真实计时器
    vi.useFakeTimers()
    try {
      downloadText('errors.csv', '"行号"\r\n"7"')
      expect(createObjectURL).toHaveBeenCalledTimes(1)
      expect(click).toHaveBeenCalledTimes(1)
      expect(revokeObjectURL).not.toHaveBeenCalled()
      vi.advanceTimersByTime(999)
      expect(revokeObjectURL).not.toHaveBeenCalled()
      vi.advanceTimersByTime(1)
      expect(revokeObjectURL).toHaveBeenCalledTimes(1)
      expect(revokeObjectURL).toHaveBeenCalledWith('blob:mock')
    } finally {
      vi.useRealTimers()
    }
  })
})
