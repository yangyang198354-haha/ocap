import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import AnimatedNumber from '@/portal/AnimatedNumber.vue'

describe('AnimatedNumber', () => {
  it('千分位与小数位格式正确', () => {
    const wrapper = mount(AnimatedNumber, { props: { value: '303622.3', decimals: 2, prefix: '¥' } })
    expect(wrapper.text()).toBe('¥303,622.30')
  })

  it('整数计数与后缀', () => {
    const wrapper = mount(AnimatedNumber, { props: { value: 2, suffix: ' 套' } })
    expect(wrapper.text()).toBe('2 套')
  })

  it('非法值按 0 处理', () => {
    const wrapper = mount(AnimatedNumber, { props: { value: 'abc', decimals: 2 } })
    expect(wrapper.text()).toBe('0.00')
  })

  it('数值更新后渲染新值', async () => {
    const wrapper = mount(AnimatedNumber, { props: { value: 1 } })
    expect(wrapper.text()).toBe('1')
    await wrapper.setProps({ value: 5 })
    await new Promise((r) => setTimeout(r, 200))
    expect(wrapper.text()).toBe('5')
  })
})
