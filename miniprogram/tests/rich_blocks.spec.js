// GROUP_D：小程序 RichBlocks 渲染（TC-UNIT-344~345）
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import RichBlocks from '@/components/RichBlocks.vue'

const blocks = [
  { type: 'paragraph', inlines: [{ text: '加粗', bold: true }, { text: '链接', href: 'https://a.b' }] },
  { type: 'heading', level: 2, inlines: [{ text: '标题' }] },
  { type: 'image', src: '/content/media/1/file?sig=x', alt: '图' },
  { type: 'quote', children: [{ type: 'paragraph', inlines: [{ text: '引用' }] }] }
]

describe('RichBlocks', () => {
  it('TC-UNIT-344 渲染段落/标题/图片/引用', () => {
    const wrapper = mount(RichBlocks, { props: { blocks, apiBase: '/api/v1' } })
    expect(wrapper.text()).toContain('加粗')
    expect(wrapper.text()).toContain('标题')
    expect(wrapper.text()).toContain('引用')
    expect(wrapper.find('image').exists()).toBe(true)
  })

  it('TC-UNIT-345 点击链接复制并提示', async () => {
    const wrapper = mount(RichBlocks, { props: { blocks, apiBase: '/api/v1' } })
    const copied = vi.fn(({ success }) => success && success())
    const toast = vi.fn()
    uni.setClipboardData = copied
    uni.showToast = toast
    wrapper.vm.openLink({ href: 'https://a.b' })
    expect(copied).toHaveBeenCalledWith(expect.objectContaining({ data: 'https://a.b' }))
    expect(toast).toHaveBeenCalledWith(expect.objectContaining({ title: '链接已复制，请在浏览器中打开' }))
  })

  // ---- GROUP_D（回流 1，续）：GR-C-003 条件 7 / GR-C-002-F07 ----
  const NESTED = [
    { type: 'quote', children: [
      { type: 'paragraph', inlines: [{ text: '引文' }] },
      { type: 'image', src: '/content/media/q1/file?sig=a', alt: '' },
      { type: 'quote', children: [{ type: 'image', src: '/content/media/q2/file?sig=b', alt: '' }] }
    ] },
    { type: 'bullet_list', items: [[
      { type: 'paragraph', inlines: [{ text: '项' }] },
      { type: 'video', src: '/content/media/v1/file?sig=c' }
    ]] },
    { type: 'ordered_list', start: 1, items: [[
      { type: 'quote', children: [{ type: 'image', src: '/content/media/l1/file?sig=d', alt: '' }] }
    ]] }
  ]

  it('TC-UNIT-399 AC-123-01：引用 / 列表内任意深度的图片与视频都输出带 API 基址的 src', () => {
    const wrapper = mount(RichBlocks, { props: { blocks: NESTED, apiBase: '/api/v1' } })
    const images = wrapper.findAll('image').map((n) => n.attributes('src'))
    const videos = wrapper.findAll('video').map((n) => n.attributes('src'))
    expect(images).toEqual(['/api/v1/content/media/q1/file?sig=a', '/api/v1/content/media/q2/file?sig=b',
      '/api/v1/content/media/l1/file?sig=d'])
    expect(videos).toEqual(['/api/v1/content/media/v1/file?sig=c'])
    for (const src of [...images, ...videos]) expect(src).not.toContain('/api/v1/api/v1')
    expect(wrapper.text()).toContain('引文')
    expect(wrapper.text()).toContain('1.')   // 有序列表序号
  })

  it('TC-UNIT-400 GR-C-002-F07：块级行距与行内行距分别作用于块与文字', () => {
    const wrapper = mount(RichBlocks, { props: { apiBase: '/api/v1', blocks: [
      { type: 'paragraph', lh: 2, align: 'center', inlines: [{ text: '甲', lh: 3 }] },
      { type: 'heading', level: 2, lh: 1.5, inlines: [{ text: '乙' }] }
    ] } })
    const blocksEls = wrapper.findAll('.rich-blocks > view')
    expect(blocksEls[0].attributes('style')).toContain('line-height: 2')
    expect(blocksEls[0].attributes('style')).toContain('text-align: center')
    expect(blocksEls[1].attributes('style')).toContain('line-height: 1.5')
    expect(blocksEls[0].find('text').attributes('style')).toContain('line-height: 3')
  })

  it('TC-UNIT-401 GR-C-002-F07：下划线 + 删除线合并为一个 text-decoration；单独使用各自保持', () => {
    const wrapper = mount(RichBlocks, { props: { apiBase: '/api/v1', blocks: [
      { type: 'paragraph', inlines: [
        { text: 'both', underline: true, strike: true },
        { text: 'under', underline: true },
        { text: 'strike', strike: true },
        { text: 'link', href: 'https://a.b', strike: true },
        { text: 'plain' }
      ] }
    ] } })
    const styles = wrapper.findAll('text').map((n) => n.attributes('style') || '')
    expect(styles[0]).toContain('text-decoration: underline line-through')
    expect(styles[1]).toContain('text-decoration: underline')
    expect(styles[1]).not.toContain('line-through')
    expect(styles[2]).toContain('text-decoration: line-through')
    expect(styles[2]).not.toContain('underline')
    expect(styles[3]).toContain('text-decoration: underline line-through')   // 链接默认下划线，与删除线合并
    expect(styles[4]).not.toContain('text-decoration')
  })

  it('TC-UNIT-402 AC-108-01：颜色 / 背景 / 字号 / 加粗 / 斜体 按行内属性渲染', () => {
    const wrapper = mount(RichBlocks, { props: { apiBase: '/api/v1', blocks: [
      { type: 'paragraph', inlines: [{ text: '红', color: '#ff0000', bg: '#ffff00', size: 20, bold: true, italic: true }] }
    ] } })
    const style = wrapper.find('text').attributes('style')
    for (const part of ['color: rgb(255, 0, 0)', 'background-color: rgb(255, 255, 0)', 'font-size: 20px',
      'font-weight: 700', 'font-style: italic']) {
      expect(style, part).toContain(part)
    }
  })
})
