// MOD-038 / US-100：RegistryImportDialog.vue 组件级用例（真实组件 + 真实 api.js，仅 mock HTTP 层）
// 溯源：AC-100-01（预检不写入）、AC-100-02（错误清单下载）、AC-100-05（结果摘要为文字）
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)

import RegistryImportDialog from '@/admin/RegistryImportDialog.vue'

const SPEC = {
  file_types: ['.csv', '.xlsx'],
  max_file_mb: 5,
  max_rows: 20000,
  excel_sheet_note: '仅读取第一个工作表',
  unit_types: [{ code: 'RESIDENCE', label: '住宅' }],
  columns: [{ name: '楼栋', required: '必填', allowed: '文本', example: '1栋' }],
  notes: []
}

const PREVIEW_OK = {
  rows_total: 3, imported: 1, updated: 0, owners_created: 3, failed: 0, errors: [], changes: [], dry_run: true
}
const PREVIEW_ERR = {
  rows_total: 4, imported: 1, updated: 0, owners_created: 2, failed: 1,
  errors: [{ row: 3, field: '手机号', reason: '手机号格式不正确' }], changes: [], dry_run: true
}

function button(text) {
  return [...document.body.querySelectorAll('button')].find((b) => b.textContent.replace(/\s/g, '') === text)
}

async function openDialog() {
  const wrapper = mount(RegistryImportDialog, {
    props: { modelValue: false },
    global: { plugins: [ElementPlus] },
    attachTo: document.body
  })
  await wrapper.setProps({ modelValue: true })
  await flushPromises()
  return wrapper
}

async function pickFile(wrapper, name = 'registry.csv') {
  const upload = wrapper.findComponent({ name: 'ElUpload' })
  const raw = new File(['楼栋,单元\n1,1'], name, { type: 'text/csv' })
  await upload.props('onChange')({ raw })
  await flushPromises()
}

describe('RegistryImportDialog', () => {
  beforeEach(() => {
    mocked.adminHttp.get.mockReset()
    mocked.adminHttp.post.mockReset()
    mocked.adminHttp.get.mockImplementation(async (url) => {
      if (url === '/admin/registry/import/spec') return SPEC
      throw new Error(`未预期的 GET ${url}`)
    })
  })
  afterEach(() => {
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('TC-UNIT-115 / AC-100-01、AC-100-05：预检显示计数且不写库，确认导入后显示结果', async () => {
    mocked.adminHttp.post
      .mockResolvedValueOnce(PREVIEW_OK)
      .mockResolvedValueOnce({ ...PREVIEW_OK, dry_run: false })
    const wrapper = await openDialog()
    expect(mocked.adminHttp.get).toHaveBeenCalledWith('/admin/registry/import/spec')
    // 未选文件：预检/确认导入均禁用
    expect(button('预检').disabled).toBe(true)
    expect(button('确认导入').disabled).toBe(true)

    await pickFile(wrapper)
    expect(button('预检').disabled).toBe(false)
    expect(button('确认导入').disabled).toBe(true)

    button('预检').click()
    await flushPromises()
    expect(mocked.adminHttp.post).toHaveBeenCalledTimes(1)
    expect(mocked.adminHttp.post.mock.calls[0][0]).toBe('/admin/registry/import')
    expect(mocked.adminHttp.post.mock.calls[0][2].params).toEqual({ dry_run: 1 })
    const text1 = document.body.textContent
    expect(text1).toContain('共 3 行：新增 1 个专有部分、更新 0 个、业主 3 位，失败 0 行（预检结果，尚未写入）')
    expect(button('确认导入').disabled).toBe(false)
    expect(document.body.textContent).not.toContain('下载错误清单')

    button('确认导入').click()
    await flushPromises()
    expect(mocked.adminHttp.post).toHaveBeenCalledTimes(2)
    expect(mocked.adminHttp.post.mock.calls[1][2].params).toBeUndefined()
    const text2 = document.body.textContent
    expect(text2).toContain('共 3 行：新增 1 个专有部分、更新 0 个、业主 3 位，失败 0 行')
    expect(text2).not.toContain('预检结果，尚未写入')
    expect(wrapper.emitted('imported')).toHaveLength(1)
    expect(wrapper.emitted('imported')[0][0].dry_run).toBe(false)
    expect(document.body.textContent).not.toContain('下载错误清单')
    wrapper.unmount()
  })

  it('TC-UNIT-116 / AC-100-02：存在失败行时出现“下载错误清单”，点击导出含失败行的 CSV', async () => {
    mocked.adminHttp.post.mockResolvedValueOnce(PREVIEW_ERR)
    const createObjectURL = vi.fn(() => 'blob:err')
    global.URL.createObjectURL = createObjectURL
    global.URL.revokeObjectURL = vi.fn()
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function () {
      anchorClick.lastDownload = this.download
    })
    let blob = null
    createObjectURL.mockImplementation((b) => { blob = b; return 'blob:err' })

    const wrapper = await openDialog()
    await pickFile(wrapper)
    button('预检').click()
    await flushPromises()

    const text = document.body.textContent
    expect(text).toContain('失败 1 行')
    expect(text).toContain('手机号格式不正确')
    const dl = button('下载错误清单')
    expect(dl).toBeTruthy()

    vi.useFakeTimers({ toFake: ['setTimeout'] })
    try {
      dl.click()
      expect(createObjectURL).toHaveBeenCalledTimes(1)
      expect(blob).toBeInstanceOf(Blob)
      expect(blob.type).toContain('text/csv')
      expect(anchorClick).toHaveBeenCalledTimes(1)
      expect(anchorClick.lastDownload).toBe('registry_import_errors.csv')
      vi.advanceTimersByTime(1000)
    } finally {
      vi.useRealTimers()
    }
    wrapper.unmount()
  })
})
