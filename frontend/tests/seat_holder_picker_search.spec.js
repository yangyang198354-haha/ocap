// 席位持有人选择：按姓名/手机号快速搜索（admin.ownerSearch）。层级：unit（真实组件 + Element Plus，仅 mock api 与级联组件）。
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'

const mocked = vi.hoisted(() => ({
  admin: { unitOptions: vi.fn(), ownerSearch: vi.fn() }
}))
vi.mock('@/shared/api', () => mocked)
vi.mock('@/portal/parts/UnitCascader.vue', () => ({
  default: {
    name: 'UnitCascader',
    props: ['modelValue', 'fetcher'],
    template: '<div class="unit-cascader-stub" />'
  }
}))

import SeatHolderPicker from '@/admin/parts/SeatHolderPicker.vue'

const flush = async () => {
  await flushPromises()
  await new Promise((resolve) => setTimeout(resolve, 0))
  await flushPromises()
}
const mountPicker = () => mount(SeatHolderPicker, { global: { plugins: [ElementPlus] } })
const searchButton = (wrapper) => wrapper.findAll('button').find((b) => b.text().includes('搜索'))
const setKeyword = async (wrapper, value) => {
  wrapper.findComponent({ name: 'ElInput' }).vm.$emit('update:modelValue', value)
  await flush()
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('SeatHolderPicker 姓名/手机号搜索（TC-UNIT-1601、1602）', () => {
  it('TC-UNIT-1601：输入关键词搜索 → 展示姓名、手机号与专有部分；点选可用业主发出 registry_owner_id；已有席位的置灰', async () => {
    mocked.admin.ownerSearch.mockResolvedValue({
      owners: [
        { owner_id: 7, name: '张三', phone: '13800001111', unit_text: '1栋1单元901号', seated: false, registered: false },
        { owner_id: 8, name: '张四', phone: '13800002222', unit_text: '1栋1单元902号', seated: true, registered: true }
      ]
    })
    const wrapper = mountPicker()
    await setKeyword(wrapper, '张三')
    await searchButton(wrapper).trigger('click')
    await flush()

    expect(mocked.admin.ownerSearch).toHaveBeenCalledWith({ keyword: '张三' })
    const text = wrapper.text()
    expect(text).toContain('张三')
    expect(text).toContain('1栋1单元901号')
    expect(text).toContain('13800001111')

    const radios = wrapper.findAll('.el-radio')
    const available = radios.find((r) => r.text().includes('张三'))
    await available.find('input').setValue(true)
    await flush()
    expect(wrapper.emitted('update:modelValue').at(-1)).toEqual([7])

    const seated = radios.find((r) => r.text().includes('张四'))
    expect(seated.find('input').attributes('disabled')).toBeDefined()
  })

  it('TC-UNIT-1602：关键词不足 2 个字符不发请求；搜索失败在弹窗内显示错误文案', async () => {
    const wrapper = mountPicker()
    await setKeyword(wrapper, '张三')
    await searchButton(wrapper).trigger('click')
    await flush()
    expect(mocked.admin.ownerSearch).toHaveBeenCalledTimes(1)

    await setKeyword(wrapper, '王')
    await searchButton(wrapper).trigger('click')
    await flush()
    expect(mocked.admin.ownerSearch).toHaveBeenCalledTimes(1)

    mocked.admin.ownerSearch.mockRejectedValue({ message: '搜索服务不可用' })
    await setKeyword(wrapper, '李四')
    await searchButton(wrapper).trigger('click')
    await flush()
    expect(wrapper.text()).toContain('搜索服务不可用')
  })
})
