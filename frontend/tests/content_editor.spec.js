// GROUP_D（回流 1，续）：内容编辑器组件级用例（TC-UNIT-383~395 前端部分）
// 真实 Toolbar / RichEditor（Tiptap + ProseMirror 跑在 jsdom 中）/ AdminContentEditor + 真实 api.js，仅 mock HTTP 层与弹窗。
// 溯源：AC-109-01/03、AC-110-01/02/03/04、AC-115-03、AC-128-03/129-01（推送结果中文状态）、GR-C-002-F02。
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus, { ElMessage, ElMessageBox } from 'element-plus'

const mocked = await vi.hoisted(async () => {
  const { createHttpMock } = await import('./http.mock.js')
  return createHttpMock()
})
vi.mock('@/shared/http', () => mocked)
vi.mock('vue-router', () => ({ useRoute: () => ({ params: { id: '7' } }), useRouter: () => ({ push: vi.fn() }) }))

import Toolbar from '@/admin/editor/Toolbar.vue'
import RichEditor from '@/admin/editor/RichEditor.vue'
import AdminContentEditor from '@/admin/AdminContentEditor.vue'
import AdminPlatforms from '@/admin/AdminPlatforms.vue'
import AdminContentPosts from '@/admin/AdminContentPosts.vue'
import MediaPicker from '@/admin/editor/MediaPicker.vue'
import { guardPastedHtml } from '@/admin/editor/pasteGuard.js'
import { toHexColor } from '@/admin/editor/colors.js'
import { pushErrorText, pushStatusText, warningsMessage } from '@/admin/editor/contentText.js'

const { adminHttp } = mocked

// ProseMirror 在 jsdom 中需要的布局 API 垫片（仅测试环境）
beforeEach(() => {
  if (!Range.prototype.getBoundingClientRect) {
    Range.prototype.getBoundingClientRect = () => ({ x: 0, y: 0, width: 0, height: 0, top: 0, left: 0, right: 0, bottom: 0 })
  }
  if (!Range.prototype.getClientRects) Range.prototype.getClientRects = () => ({ length: 0, item: () => null, [Symbol.iterator]: function* () {} })
  if (!document.elementFromPoint) document.elementFromPoint = () => null
})
afterEach(() => {
  document.body.innerHTML = ''
  vi.restoreAllMocks()
  vi.useRealTimers()
})

const para = (text, marks) => ({ type: 'paragraph', content: [{ type: 'text', text, ...(marks ? { marks } : {}) }] })
const docOf = (...blocks) => ({ type: 'doc', content: blocks })
const buttonByText = (root, text) => root.findAll('button').find((b) => b.text().replace(/\s/g, '') === text)

async function mountEditor(initial = docOf(para('原文'))) {
  const wrapper = mount(RichEditor, { props: { modelValue: initial }, global: { plugins: [ElementPlus] }, attachTo: document.body })
  await flushPromises()
  const editor = wrapper.findComponent(Toolbar).props('editor')
  return { wrapper, editor }
}

describe('工具栏功能清单（AC-110-01 / AC-110-04）', () => {
  it('TC-UNIT-383：提供且仅提供基础格式清单；不含表格、代码块、公式、表情、卡片', async () => {
    const wrapper = mount(Toolbar, { props: { editor: null }, global: { plugins: [ElementPlus] } })
    await flushPromises()
    const labels = wrapper.findAll('button').map((b) => b.text().replace(/\s/g, ''))
    // 加粗/斜体/下划线/删除线、对齐、列表/引用/分割线、撤销/重做/清除格式、图片/视频/分页/链接
    expect(labels).toEqual(['B', 'I', 'U', 'S', '左', '中', '右', '两端', '无序', '有序', '引用', '分割线',
      '清除', '清除', '撤销', '重做', '清除格式', '图片', '视频', '分页', '链接'])
    // 标题层级：正文 + 标题1~4（不含 5、6 级）
    const options = wrapper.findAllComponents({ name: 'ElOption' }).map((o) => o.props('label'))
    expect(options).toEqual(['正文', '标题1', '标题2', '标题3', '标题4'])
    // 文字色 / 背景色 = 取色器；字号、行距 = 输入框
    expect(wrapper.findAllComponents({ name: 'ElColorPicker' })).toHaveLength(2)
    const placeholders = wrapper.findAll('input').map((i) => i.attributes('placeholder')).filter(Boolean)
    expect(placeholders).toEqual(expect.arrayContaining(['字号', '行距']))
    const text = wrapper.text()
    for (const banned of ['表格', '代码', '公式', '表情', '卡片']) expect(text).not.toContain(banned)
    expect(wrapper.html()).not.toMatch(/table|codeBlock|formula|emoji|card/i)
    wrapper.unmount()
  })

  it('TC-UNIT-384：RichEditor 注册的扩展不含表格、代码、公式', async () => {
    const { wrapper, editor } = await mountEditor()
    const names = editor.extensionManager.extensions.map((e) => e.name)
    for (const needed of ['bold', 'italic', 'underline', 'strike', 'heading', 'textAlign', 'color', 'backgroundColor',
      'fontSize', 'lineHeight', 'link', 'bulletList', 'orderedList', 'blockquote', 'horizontalRule', 'image',
      'video', 'undoRedo']) {
      expect(names, needed).toContain(needed)
    }
    for (const banned of ['table', 'tableRow', 'code', 'codeBlock', 'mathematics', 'emoji']) {
      expect(names, banned).not.toContain(banned)
    }
    wrapper.unmount()
  })
})

describe('取色器（AC-109-01 / ADR-062）', () => {
  function fakeEditor() {
    const calls = []
    const chain = new Proxy({}, {
      get: (_t, name) => (name === 'run' ? () => true : (...args) => { calls.push([name, ...args]); return chain })
    })
    return { calls, editor: { chain: () => chain, isActive: () => false, getAttributes: () => ({}) } }
  }

  it('TC-UNIT-385：取色器输出 #hex 直接设置；rgb() 归一化；非法值不设置并清除', async () => {
    const { calls, editor } = fakeEditor()
    const wrapper = mount(Toolbar, { props: { editor }, global: { plugins: [ElementPlus] } })
    const [textPicker, bgPicker] = wrapper.findAllComponents({ name: 'ElColorPicker' })
    textPicker.vm.$emit('change', '#d0021b')
    textPicker.vm.$emit('change', 'rgb(255, 0, 0)')
    bgPicker.vm.$emit('change', '#F8E71C')
    bgPicker.vm.$emit('change', 'rgba(0, 0, 0, 0.5)')
    expect(calls.filter((c) => c[0] === 'setColor')).toEqual([['setColor', '#d0021b'], ['setColor', '#ff0000']])
    expect(calls.filter((c) => c[0] === 'setBackgroundColor'))
      .toEqual([['setBackgroundColor', '#F8E71C'], ['setBackgroundColor', '#00000080']])
    calls.length = 0
    textPicker.vm.$emit('change', 'red')
    textPicker.vm.$emit('change', 'url(javascript:alert(1))')
    bgPicker.vm.$emit('change', 'rgb(300, 0, 0)')
    expect(calls.map((c) => c[0])).not.toContain('setColor')
    expect(calls.map((c) => c[0])).not.toContain('setBackgroundColor')
    expect(calls.filter((c) => c[0] === 'unsetColor')).toHaveLength(2)
    expect(calls.filter((c) => c[0] === 'unsetBackgroundColor')).toHaveLength(1)
    wrapper.unmount()
  })

  it('TC-UNIT-386：真实编辑器经取色器设置颜色后，文档中为 #hex 且保存前后一致（AC-109-01）', async () => {
    const { wrapper, editor } = await mountEditor(docOf(para('红色')))
    editor.commands.selectAll()
    const [textPicker] = wrapper.findAllComponents({ name: 'ElColorPicker' })
    textPicker.vm.$emit('change', 'rgb(255, 0, 0)')
    await flushPromises()
    const marks = editor.getJSON().content[0].content[0].marks
    expect(marks).toHaveLength(1)
    expect(marks[0].type).toBe('textStyle')
    expect(marks[0].attrs.color).toBe('#ff0000')   // 其余属性为 null（服务端视为未设置，不产生警告）
    expect(JSON.stringify(wrapper.emitted('update:modelValue').at(-1)[0])).toContain('#ff0000')
    wrapper.unmount()
  })

  it('TC-UNIT-387：toHexColor 与共享向量口径一致（不扩张白名单）', () => {
    expect(toHexColor('rgb(255, 0, 0)')).toBe('#ff0000')
    expect(toHexColor('rgba(0, 0, 0, 0.5)')).toBe('#00000080')
    expect(toHexColor('#abc')).toBe('#abc')
    for (const bad of ['red', 'rgb(256,0,0)', 'rgba(1,2,3,1.5)', 'url(x)', '', null, undefined, 12]) {
      expect(toHexColor(bad), String(bad)).toBeNull()
    }
  })
})

describe('粘贴守卫（ADR-062）', () => {
  it('TC-UNIT-388：rgb 归一化、非法颜色声明删除文字保留、外链图片丢弃并计数、脚本移除', () => {
    const html = '<p style="color: rgb(255, 0, 0); background-color: red; text-align: center">甲</p>'
      + '<img src="https://evil.example/x.png"><img src="data:image/png;base64,AAAA">'
      + '<img src="/api/v1/content/media/x/file" data-media-id="m1">'
      + '<script>alert(1)</script><iframe src="//x"></iframe><p>乙</p>'
    const result = guardPastedHtml(html)
    expect(result.droppedImages).toBe(2)
    expect(result.html).toContain('color: #ff0000')
    expect(result.html).not.toMatch(/rgb\(/)
    expect(result.html).not.toContain('background-color')
    expect(result.html).toContain('text-align: center')
    expect(result.html).toContain('甲')
    expect(result.html).toContain('乙')
    expect(result.html).toContain('data-media-id="m1"')
    expect(result.html).not.toMatch(/evil\.example|<script|<iframe|data:image/)
  })

  it('TC-UNIT-389：经真实编辑器粘贴 HTML：颜色成为 #hex、外链图片不进入文档并触发 paste-dropped', async () => {
    if (typeof globalThis.ClipboardEvent === 'undefined') {
      globalThis.ClipboardEvent = class extends Event {}   // jsdom 未实现，ProseMirror pasteHTML 需要
    }
    const { wrapper, editor } = await mountEditor(docOf(para('开头')))
    editor.view.pasteHTML('<p><span style="color: rgb(0, 128, 0)">绿字</span></p><img src="https://evil.example/a.png">')
    await flushPromises()
    const json = JSON.stringify(editor.getJSON())
    expect(json).toContain('绿字')
    expect(json).toContain('#008000')
    expect(json).not.toMatch(/rgb\(|evil\.example/)
    expect(editor.getJSON().content.some((n) => n.type === 'image')).toBe(false)
    expect(wrapper.emitted('paste-dropped')[0][0]).toEqual({ images: 1 })
    wrapper.unmount()
  })
})

describe('清除格式 / 撤销重做 / 链接（AC-110-02、AC-110-03、AC-109-03）', () => {
  it('TC-UNIT-390：清除格式后回到默认样式，文字不变（加粗、字号、背景色）', async () => {
    const { wrapper, editor } = await mountEditor(docOf(para('保持文字')))
    editor.commands.selectAll()
    editor.chain().focus().toggleBold().setFontSize('24px').setBackgroundColor('#f8e71c').run()
    const before = JSON.stringify(editor.getJSON().content[0].content[0].marks)
    expect(before).toContain('bold')
    expect(before).toContain('24px')
    expect(before).toContain('#f8e71c')
    editor.commands.selectAll()
    await buttonByText(wrapper.findComponent(Toolbar), '清除格式').trigger('click')
    await flushPromises()
    const node = editor.getJSON().content[0].content[0]
    expect(node.text).toBe('保持文字')
    expect(node.marks ?? []).toEqual([])
    wrapper.unmount()
  })

  it('TC-UNIT-391：两步编辑后撤销一次回到上一步，重做一次回到重做后状态', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-01-01T00:00:00Z'))
    const { wrapper, editor } = await mountEditor(docOf(para('起点')))
    const text = () => editor.getText()
    editor.commands.focus('end')
    editor.commands.insertContent('甲')
    vi.setSystemTime(new Date('2026-01-01T00:00:05Z'))   // 超过历史分组间隔，成为独立一步
    editor.commands.insertContent('乙')
    expect(text()).toBe('起点甲乙')
    const toolbar = wrapper.findComponent(Toolbar)
    await buttonByText(toolbar, '撤销').trigger('click')
    expect(text()).toBe('起点甲')
    await buttonByText(toolbar, '重做').trigger('click')
    expect(text()).toBe('起点甲乙')
    wrapper.unmount()
  })

  it('TC-UNIT-392：链接地址格式明显无效时不添加链接并提示“网址无效”；有效地址添加成功', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper, editor } = await mountEditor(docOf(para('链接文字')))
    const toolbar = wrapper.findComponent(Toolbar)
    for (const bad of ['javascript:alert(1)', 'www.example.com', 'ftp://x']) {
      editor.commands.selectAll()
      vi.spyOn(window, 'prompt').mockReturnValueOnce(bad)
      await buttonByText(toolbar, '链接').trigger('click')
      expect(JSON.stringify(editor.getJSON()), bad).not.toContain('"link"')
    }
    expect(error).toHaveBeenCalledTimes(3)
    expect(error).toHaveBeenCalledWith('网址无效')
    editor.commands.selectAll()
    vi.spyOn(window, 'prompt').mockReturnValueOnce('https://example.com/a')
    await buttonByText(toolbar, '链接').trigger('click')
    const marks = editor.getJSON().content[0].content[0].marks
    expect(marks.find((m) => m.type === 'link').attrs.href).toBe('https://example.com/a')
    wrapper.unmount()
  })

  it('TC-UNIT-393：链接地址为空（确认空输入）时不添加链接并提示“网址无效”；取消输入则静默', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    const { wrapper, editor } = await mountEditor(docOf(para('链接文字')))
    const toolbar = wrapper.findComponent(Toolbar)
    editor.commands.selectAll()
    vi.spyOn(window, 'prompt').mockReturnValueOnce(null)   // 点“取消”
    await buttonByText(toolbar, '链接').trigger('click')
    expect(error).not.toHaveBeenCalled()
    vi.spyOn(window, 'prompt').mockReturnValueOnce('')     // 点“确定”但未填写
    await buttonByText(toolbar, '链接').trigger('click')
    expect(JSON.stringify(editor.getJSON())).not.toContain('"link"')
    expect(error).toHaveBeenCalledWith('网址无效')
    wrapper.unmount()
  })
})

// ---- 页面级：AdminContentEditor ----
const POST = {
  id: 7, title: '公告', doc: docOf(para('已有正文')), style_key: 'builtin:classic',
  media_urls: {}, text_confirmed: false
}

function wireHttp({ patch } = {}) {
  adminHttp.get.mockReset(); adminHttp.post.mockReset(); adminHttp.patch.mockReset()
  adminHttp.get.mockImplementation(async (url, arg) => {
    if (url === '/admin/content/posts/7') return POST
    if (url === '/admin/content/style-templates') return [{ key: 'builtin:classic', name: '经典' }]
    if (url === '/admin/content/llm/options') return []
    if (url === '/admin/content/prompt-templates') return []
    if (url === '/admin/content/platform-accounts') {
      return [{ platform: 'wechat_mp', label: '微信公众号', account: { id: 1, display_name: '号', auth_status: 'NORMAL' } },
        { platform: 'xiaohongshu', label: '小红书', account: { id: 2, display_name: '红', auth_status: 'NORMAL' } }]
    }
    throw new Error(`未预期的 GET ${url} ${JSON.stringify(arg)}`)
  })
  adminHttp.patch.mockImplementation(patch || (async () => ({ ...POST, warnings: [], warning_total: 0 })))
  adminHttp.post.mockImplementation(async (url) => ({ ok: true, url }))
}

async function mountPage() {
  const wrapper = mount(AdminContentEditor, { global: { plugins: [ElementPlus], mocks: { $router: { push: vi.fn() } } }, attachTo: document.body })
  await flushPromises()
  return wrapper
}
const postCalls = (suffix) => adminHttp.post.mock.calls.filter(([url]) => url.endsWith(suffix))

describe('保存失败时中止发布 / 确认（GR-C-002-F02）', () => {
  it('TC-UNIT-394：保存失败（400 CONTENT_INVALID_DOC）→ 不发布、不确认文案，并给出带位置的提示', async () => {
    const error = vi.spyOn(ElMessage, 'error').mockImplementation(() => {})
    wireHttp({
      patch: async () => { throw Object.assign(new Error('bad'), { code: 'CONTENT_INVALID_DOC', details: { block_index: 0, block_type: 'paragraph', reason: 'LIMIT' } }) }
    })
    const wrapper = await mountPage()
    await buttonByText(wrapper, '发布').trigger('click'); await flushPromises()
    await buttonByText(wrapper, '确认文案').trigger('click'); await flushPromises()
    expect(adminHttp.patch).toHaveBeenCalledTimes(2)
    expect(postCalls('/publish')).toHaveLength(0)
    expect(postCalls('/confirm-text')).toHaveLength(0)
    expect(error).toHaveBeenCalledWith(expect.stringContaining('第 1 个块（段落）'))
    wrapper.unmount()
  })

  it('TC-UNIT-395：保存成功才发布 / 确认；保存带 warnings 时用服务端规范化文档替换并提示', async () => {
    const warning = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const normalized = docOf(para('已有正文', [{ type: 'textStyle', attrs: { color: '#ff0000' } }]))
    wireHttp({ patch: async () => ({ ...POST, doc: normalized, warnings: [{ block_index: 0, reason: 'COLOR', action: 'NORMALIZED' }], warning_total: 1 }) })
    const wrapper = await mountPage()
    await buttonByText(wrapper, '发布').trigger('click'); await flushPromises()
    expect(postCalls('/publish')).toHaveLength(1)
    expect(adminHttp.patch.mock.invocationCallOrder[0]).toBeLessThan(adminHttp.post.mock.invocationCallOrder[0])
    expect(warning).toHaveBeenCalledWith(expect.stringContaining('已自动处理/忽略 1 处不支持的格式'))
    expect(JSON.stringify(wrapper.vm.doc)).toContain('#ff0000')   // 编辑器内容已被规范化文档替换
    await buttonByText(wrapper, '确认文案').trigger('click'); await flushPromises()
    expect(postCalls('/confirm-text')).toHaveLength(1)
    wrapper.unmount()
  })
})

describe('放入编辑器的覆盖确认（AC-115-03）', () => {
  it('TC-UNIT-396：已有正文时先确认“将覆盖当前正文”，取消则正文不变；确认才覆盖', async () => {
    wireHttp()
    const wrapper = await mountPage()
    wrapper.vm.generatedText = '生成文案第一段\n\n生成文案第二段'
    await flushPromises()
    const confirm = vi.spyOn(ElMessageBox, 'confirm').mockRejectedValueOnce('cancel')
    const original = JSON.stringify(wrapper.vm.doc)
    await buttonByText(wrapper, '放入编辑器').trigger('click'); await flushPromises()
    expect(confirm).toHaveBeenCalledWith('将覆盖当前正文，是否继续？', '提示', { type: 'warning' })
    expect(JSON.stringify(wrapper.vm.doc)).toBe(original)

    confirm.mockResolvedValueOnce('confirm')
    await buttonByText(wrapper, '放入编辑器').trigger('click'); await flushPromises()
    expect(wrapper.vm.doc.content.map((b) => b.content[0].text)).toEqual(['生成文案第一段', '生成文案第二段'])
    wrapper.unmount()
  })
})

describe('推送结果中文状态（AC-128-03 / AC-129-01）', () => {
  it('TC-UNIT-397：对话框中的推送结果显示中文状态与失败原因，不出现英文状态码', async () => {
    wireHttp()
    const pushes = [
      { id: 1, platform: 'wechat_mp', mode: 'AUTO', status: 'FAILED', error_code: 'AUTH_EXPIRED', error_message: '', unsupported: [] },
      { id: 2, platform: 'xiaohongshu', mode: 'MANUAL', status: 'MANUAL_REQUIRED', error_code: '', error_message: '', unsupported: ['page_break', 'style_not_carried'] }
    ]
    adminHttp.post.mockImplementation(async (url) => (url.endsWith('/drafts') ? { batch_id: 'b', job_id: null, pushes } : {}))
    const wrapper = await mountPage()
    await buttonByText(wrapper, '一键保存到草稿箱').trigger('click'); await flushPromises()
    wrapper.vm.selectedAccounts = [1, 2]
    await flushPromises()
    const start = [...document.body.querySelectorAll('button')].find((b) => b.textContent.replace(/\s/g, '') === '开始保存')
    start.click(); await flushPromises()
    const text = document.body.textContent
    for (const expected of ['微信公众号', '小红书', '失败', '需人工粘贴', '认证已失效，请重新认证', '分页、版式样式']) {
      expect(text, expected).toContain(expected)
    }
    for (const code of ['FAILED', 'MANUAL_REQUIRED', 'AUTH_EXPIRED', 'wechat_mp', 'xiaohongshu']) {
      expect(text, code).not.toContain(code)
    }
    wrapper.unmount()
  })

  it('TC-UNIT-398：状态 / 原因 / 警告文案映射纯函数', () => {
    expect(['PENDING', 'SENDING', 'SAVED', 'FAILED', 'UNKNOWN', 'MANUAL_REQUIRED'].map(pushStatusText))
      .toEqual(['排队中', '发送中', '成功', '失败', '结果未知', '需人工粘贴'])
    expect(pushErrorText({ error_code: 'IP_NOT_WHITELISTED' })).toBe('服务器出口 IP 未加入公众号 IP 白名单')
    expect(pushErrorText({ error_code: 'UPSTREAM', error_message: 'errcode=1' })).toBe('平台返回错误：errcode=1')
    expect(warningsMessage([], 0, null)).toBe('')
    expect(warningsMessage([{ block_index: 1, reason: 'LINK' }], 1, docOf(para('a'), para('b'))))
      .toBe('已自动处理/忽略 1 处不支持的格式：第 2 个块（段落） 链接地址无效')
  })
})

describe('页面入口与平台账户页（AC-124-07、AC-127-02/03/05、AC-128-04）', () => {
  it('TC-UNIT-403：视频生成只有“生成视频”入口，不提供分镜编辑 / 裁剪 / 调序（AC-124-07）', async () => {
    wireHttp()
    const wrapper = await mountPage()
    const labels = wrapper.findAll('button').map((b) => b.text().replace(/\s/g, ''))
    expect(labels).toContain('生成视频')
    for (const banned of ['分镜', '裁剪', '调序', '排序']) {
      expect(wrapper.text()).not.toContain(banned)
    }
    wrapper.unmount()
  })

  it('TC-UNIT-404：未勾选任何平台时“开始保存”可点击，提示“请至少选择一个平台”且不发起保存（AC-128-04）', async () => {
    wireHttp()
    const warning = vi.spyOn(ElMessage, 'warning').mockImplementation(() => {})
    const wrapper = await mountPage()
    await buttonByText(wrapper, '一键保存到草稿箱').trigger('click'); await flushPromises()
    const start = [...document.body.querySelectorAll('button')].find((b) => b.textContent.replace(/\s/g, '') === '开始保存')
    expect(start.disabled).toBe(false)
    start.click(); await flushPromises()
    expect(warning).toHaveBeenCalledWith('请至少选择一个平台')
    expect(adminHttp.post.mock.calls.filter(([url]) => url.endsWith('/drafts'))).toHaveLength(0)
    warning.mockRestore()
    wrapper.unmount()
  })

  const PLATFORM_LIST = [
    { platform: 'wechat_mp', label: '微信公众号', capability: 'AUTO_DRAFT',
      credential_fields: [{ key: 'appid', label: 'AppID' }, { key: 'appsecret', label: 'AppSecret' }],
      account: { id: 1, display_name: '小区号', auth_status: 'EXPIRED', secret_saved: { appid: true, appsecret: true } } },
    { platform: 'xiaohongshu', label: '小红书', capability: 'MANUAL_EXPORT',
      credential_fields: [{ key: 'credential', label: '认证信息（预留）' }], account: null },
    { platform: 'toutiao', label: '今日头条', capability: 'MANUAL_EXPORT',
      credential_fields: [{ key: 'credential', label: '认证信息（预留）' }], account: null }
  ]

  it('TC-UNIT-405：平台账户页仅三个平台、失效账户显示“失效”与重新认证提示、认证信息不回显、无“检测有效性”入口', async () => {
    adminHttp.get.mockReset()
    adminHttp.get.mockResolvedValue(PLATFORM_LIST)
    const wrapper = mount(AdminPlatforms, { global: { plugins: [ElementPlus] }, attachTo: document.body })
    await flushPromises()
    const titles = wrapper.findAll('strong').map((n) => n.text())
    expect(titles).toEqual(['微信公众号', '小红书', '今日头条'])          // AC-126-04：不含微博、视频号
    const text = wrapper.text()
    expect(text).toContain('失效')                                         // AC-127-03：账户标记
    expect(text).toContain('认证已失效，请重新录入认证信息')
    for (const banned of ['检测', '校验账户', '验证有效']) expect(text).not.toContain(banned)   // AC-127-05
    const inputs = wrapper.findAll('input').filter((i) => i.attributes('placeholder')?.includes('已保存'))
    expect(inputs).toHaveLength(2)
    for (const input of inputs) expect(input.element.value).toBe('')    // AC-127-02：页面不回显原文
    wrapper.unmount()
  })

  it('TC-UNIT-406：覆盖更新认证信息只提交填写的字段（未填不覆盖），提交后重新加载', async () => {
    adminHttp.get.mockReset(); adminHttp.patch.mockReset()
    adminHttp.get.mockResolvedValue(PLATFORM_LIST)
    adminHttp.patch.mockResolvedValue({})
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const wrapper = mount(AdminPlatforms, { global: { plugins: [ElementPlus] }, attachTo: document.body })
    await flushPromises()
    const secret = wrapper.findAll('input').find((i) => i.attributes('placeholder')?.includes('AppSecret'))
    await secret.setValue('NEW-SECRET-VALUE')
    await buttonByText(wrapper, '保存').trigger('click'); await flushPromises()
    expect(adminHttp.patch).toHaveBeenCalledWith('/admin/content/platform-accounts/1',
      { display_name: undefined, credentials: { appsecret: 'NEW-SECRET-VALUE' } })
    expect(adminHttp.get).toHaveBeenCalledTimes(2)   // 初次加载 + 保存后刷新
    wrapper.unmount()
  })
})

describe('删除确认与素材选择器（AC-106-03、AC-121-01/03、AC-111-01）', () => {
  it('TC-UNIT-407：删除二次确认取消时不发起删除（内容仍在）；确认后才删除', async () => {
    adminHttp.get.mockReset(); adminHttp.delete.mockReset()
    adminHttp.get.mockResolvedValue({ results: [{ id: 5, title: '待删公告', status: 'DRAFT' }], count: 1 })
    adminHttp.delete.mockResolvedValue({})
    vi.spyOn(ElMessage, 'success').mockImplementation(() => {})
    const confirm = vi.spyOn(ElMessageBox, 'confirm').mockRejectedValueOnce('cancel')
    const wrapper = mount(AdminContentPosts, { global: { plugins: [ElementPlus], mocks: { $router: { push: vi.fn() } } }, attachTo: document.body })
    await flushPromises()
    await buttonByText(wrapper, '删除').trigger('click'); await flushPromises()
    expect(confirm).toHaveBeenCalledWith('确认删除「待删公告」？', '删除确认', { type: 'warning' })
    expect(adminHttp.delete).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('待删公告')
    confirm.mockResolvedValueOnce('confirm')
    await buttonByText(wrapper, '删除').trigger('click'); await flushPromises()
    expect(adminHttp.delete).toHaveBeenCalledWith('/admin/content/posts/5')
    wrapper.unmount()
  })

  async function openPicker(items) {
    adminHttp.get.mockReset()
    adminHttp.get.mockResolvedValue({ results: items })
    const wrapper = mount(MediaPicker, { global: { plugins: [ElementPlus] }, attachTo: document.body })
    wrapper.vm.open('IMAGE')
    await flushPromises()
    return wrapper
  }

  it('TC-UNIT-408：素材库为空时显示“素材库为空”且不报错（AC-121-03）', async () => {
    const wrapper = await openPicker([])
    expect(document.body.textContent).toContain('素材库为空')
    expect(adminHttp.get).toHaveBeenCalledWith('/admin/content/media', { params: { media_type: 'IMAGE', page_size: 100 } })
    wrapper.unmount()
  })

  it('TC-UNIT-409：上传与 AI 生成的图片均可选，选中后抛出 selected 且可插入编辑器正文（AC-121-01 / AC-111-01）', async () => {
    const items = [
      { id: 'u1', media_type: 'IMAGE', source: 'UPLOAD', title: '上传图', url: '/api/v1/content/media/u1/file?sig=a' },
      { id: 'a1', media_type: 'IMAGE', source: 'AI_GENERATED', title: 'AI 图', url: '/api/v1/content/media/a1/file?sig=b' }
    ]
    const picker = await openPicker(items)
    const cards = [...document.body.querySelectorAll('.media-card')]
    expect(cards.map((c) => c.textContent.trim())).toEqual(['上传图', 'AI 图'])
    cards[1].click(); await flushPromises()
    const [payload] = picker.emitted('selected')[0]
    expect(payload).toEqual({ kind: 'image', mediaId: 'a1', url: '/api/v1/content/media/a1/file?sig=b' })
    picker.unmount()

    const { wrapper, editor } = await mountEditor(docOf(para('正文')))
    wrapper.vm.insertMedia(payload.kind, payload.mediaId, payload.url)
    await flushPromises()
    const image = editor.getJSON().content.find((n) => n.type === 'image')
    expect(image.attrs.mediaId).toBe('a1')
    expect(image.attrs.src).toBe(payload.url)
    wrapper.unmount()
  })
})
