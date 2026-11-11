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
})
