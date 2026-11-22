// ocap_brand_layout GROUP_D（MOD-131）：SideNav / SubNavBar 组件行为（IFC-318/319）。
// 层级：integration（真实 vue-router + 真实组件，仅内存路由）。TC-INT-801 起。
import { afterEach, describe, expect, it } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import SideNav from '@/layout/SideNav.vue'
import SubNavBar from '@/layout/SubNavBar.vue'
import { ADMIN_MENU, PORTAL_MENU, visibleMenu } from '@/layout/menus'

const FULL = visibleMenu(PORTAL_MENU, { isCommittee: true })

async function mountNav(path, { menu = FULL, props = {} } = {}) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }]
  })
  router.push(path)
  await router.isReady()
  const wrapper = mount(SideNav, { props: { menu, ...props }, global: { plugins: [router] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, router }
}
const toggleOf = (wrapper, label) => wrapper.findAll('button.side-group-toggle').find((b) => b.text().includes(label))
const activeLabels = (wrapper) => wrapper.findAll('.side-item.is-active .side-label').map((e) => e.text())

afterEach(() => { document.body.innerHTML = '' })

describe('SideNav 展开/收起（US-216）', () => {
  it('TC-INT-801 / AC-216-01：主页默认全部收起——三个有二级项的一级 aria-expanded=false，页面没有任何二级列表', async () => {
    const { wrapper } = await mountNav('/')
    const toggles = wrapper.findAll('button.side-group-toggle')
    expect(toggles.map((b) => b.find('.side-label').text())).toEqual(['我的房屋', '决议', '报销/备用金'])
    for (const b of toggles) expect(b.attributes('aria-expanded')).toBe('false')
    expect(wrapper.findAll('ul.side-sub')).toHaveLength(0)
    expect(wrapper.findAll('.side-sub-item')).toHaveLength(0)
    expect(activeLabels(wrapper)).toEqual(['主页'])
    wrapper.unmount()
  })

  it('TC-INT-802 / AC-216-02：点击"决议"展开 3 个二级项，再点收起；全程不导航，二级列表收起时不渲染', async () => {
    const { wrapper, router } = await mountNav('/')
    await toggleOf(wrapper, '决议').trigger('click')
    expect(toggleOf(wrapper, '决议').attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('ul.side-sub').attributes('id')).toBe('side-sub-resolutions')
    expect(toggleOf(wrapper, '决议').attributes('aria-controls')).toBe('side-sub-resolutions')
    expect(wrapper.findAll('.side-sub-item').map((a) => a.find('.side-label').text())).toEqual(['公开决议', '我发起的', '待我表决'])
    expect(router.currentRoute.value.path).toBe('/')
    await toggleOf(wrapper, '决议').trigger('click')
    expect(toggleOf(wrapper, '决议').attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('ul.side-sub').exists()).toBe(false)
    expect(router.currentRoute.value.path).toBe('/')
    wrapper.unmount()
  })

  it('TC-INT-803 / AC-216-03：在"我的房屋"展开状态下点"决议"——同时只展开一个（决议展开，我的房屋收起）', async () => {
    const { wrapper } = await mountNav('/')
    await toggleOf(wrapper, '我的房屋').trigger('click')
    // 改写（ocap_navigation_ia ADR-166）：二级项收敛为 3 项
    expect(wrapper.findAll('.side-sub-item')).toHaveLength(3)
    expect(wrapper.findAll('.side-sub-item').map((a) => a.text().replace(/\d+$/, '').trim())).toEqual(
      ['我的身份与房屋', '我的认证与申述', '我的同住人申请']
    )
    await toggleOf(wrapper, '决议').trigger('click')
    expect(toggleOf(wrapper, '我的房屋').attributes('aria-expanded')).toBe('false')
    expect(toggleOf(wrapper, '决议').attributes('aria-expanded')).toBe('true')
    expect(wrapper.findAll('ul.side-sub')).toHaveLength(1)
    expect(wrapper.findAll('.side-sub-item')).toHaveLength(3)
    wrapper.unmount()
  })

  it('TC-INT-804 / AC-299-02、AC-216-04：直达 /units/appeal（刷新）——"我的房屋"自动展开并高亮"我的认证与申述"，其余一级仍收起；旧地址 /units/appeals 无独立菜单项', async () => {
    const { wrapper } = await mountNav('/units/appeal')
    expect(toggleOf(wrapper, '我的房屋').attributes('aria-expanded')).toBe('true')
    expect(toggleOf(wrapper, '决议').attributes('aria-expanded')).toBe('false')
    expect(toggleOf(wrapper, '报销/备用金').attributes('aria-expanded')).toBe('false')
    const active = wrapper.findAll('.side-sub-item.is-active')
    expect(active).toHaveLength(1)
    expect(active[0].text()).toContain('我的认证与申述')
    expect(active[0].attributes('aria-current')).toBe('page')
    expect(activeLabels(wrapper)).toEqual(['我的房屋'])
    wrapper.unmount()
  })

  it('TC-INT-805 / AC-215-04：位于 /resolutions/12 详情页——"决议"展开且一级高亮，二级项无任何一项高亮', async () => {
    const { wrapper } = await mountNav('/resolutions/12')
    expect(toggleOf(wrapper, '决议').attributes('aria-expanded')).toBe('true')
    expect(activeLabels(wrapper)).toEqual(['决议'])
    expect(wrapper.findAll('.side-sub-item')).toHaveLength(3)
    expect(wrapper.findAll('.side-sub-item.is-active')).toHaveLength(0)
    wrapper.unmount()
  })

  it('TC-INT-806 / AC-216-04：路由变化时展开规则重新计算——进入决议后展开决议，回到主页后全部收起', async () => {
    const { wrapper, router } = await mountNav('/units')
    expect(toggleOf(wrapper, '我的房屋').attributes('aria-expanded')).toBe('true')
    await router.push('/resolutions/mine')
    await flushPromises()
    expect(toggleOf(wrapper, '我的房屋').attributes('aria-expanded')).toBe('false')
    expect(toggleOf(wrapper, '决议').attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('.side-sub-item.is-active').text()).toContain('我发起的')
    await router.push('/')
    await flushPromises()
    expect(wrapper.findAll('ul.side-sub')).toHaveLength(0)
    wrapper.unmount()
  })
})

describe('SideNav 一级项与高亮（US-210、217、229）', () => {
  it('TC-INT-807 / AC-217-01：6 个无二级项的一级是 a.side-item，没有展开箭头与空二级列表', async () => {
    const { wrapper } = await mountNav('/')
    const links = wrapper.findAll('a.side-item')
    expect(links.map((a) => a.find('.side-label').text())).toEqual(['主页', '投票/调查', '收入表', '财务报表', '待办', '信息公开'])
    for (const a of links) expect(a.find('.side-caret').exists()).toBe(false)
    expect(wrapper.findAll('.side-caret')).toHaveLength(3)
    expect(wrapper.findAll('ul.side-sub')).toHaveLength(0)
    wrapper.unmount()
  })

  it('TC-INT-808 / AC-210-03、AC-217-02：点击无二级项的一级一次直达（地址变为 /polls）；进入 /polls/3 后"投票/调查"仍是唯一高亮项', async () => {
    const { wrapper, router } = await mountNav('/')
    await wrapper.findAll('a.side-item').find((a) => a.text().includes('投票/调查')).trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.path).toBe('/polls')
    await router.push('/polls/3')
    await flushPromises()
    expect(activeLabels(wrapper)).toEqual(['投票/调查'])
    expect(wrapper.find('.side-item.is-active').attributes('aria-current')).toBe('page')
    wrapper.unmount()
  })

  it('TC-INT-809 / AC-210-02、AC-229-02：/info/5 仅"信息公开"高亮；任意时刻一级高亮数 = 1', async () => {
    const { wrapper, router } = await mountNav('/info/5')
    expect(activeLabels(wrapper)).toEqual(['信息公开'])
    for (const p of ['/', '/units/pick', '/claims/todo', '/reports', '/tasks', '/income']) {
      await router.push(p)
      await flushPromises()
      expect(wrapper.findAll('.side-item.is-active'), p).toHaveLength(1)
    }
    wrapper.unmount()
  })

  it('TC-INT-810 / AC-235-01（旧 AC-214-03）：badges.pendingReview=2 时仅"我的身份与房屋"二级项显示角标 2；为 0 或缺省不显示', async () => {
    // 改写：旧断言角标在"待我审批的同住人申请"项 → 新断言角标在"我的身份与房屋"项（Q-IP-04=A）
    const { wrapper } = await mountNav('/units', { props: { badges: { pendingReview: 2 } } })
    const badges = wrapper.findAll('.side-badge')
    expect(badges).toHaveLength(1)
    expect(badges[0].text()).toBe('2')
    expect(badges[0].element.closest('a').textContent).toContain('我的身份与房屋')
    expect(wrapper.text()).not.toContain('待我审批的同住人申请')
    await wrapper.setProps({ badges: { pendingReview: 0 } })
    expect(wrapper.findAll('.side-badge')).toHaveLength(0)
    await wrapper.setProps({ badges: {} })
    expect(wrapper.findAll('.side-badge')).toHaveLength(0)
    wrapper.unmount()
  })

  it('TC-INT-811 / REQ-NFUNC-039：键盘——一级与二级项均为原生 button/a（可 Tab 聚焦）；Esc 收起所属一级并把焦点还给其按钮', async () => {
    const { wrapper } = await mountNav('/')
    const toggle = toggleOf(wrapper, '决议')
    await toggle.trigger('click')
    for (const el of wrapper.findAll('.side-item, .side-sub-item')) expect(['BUTTON', 'A']).toContain(el.element.tagName)
    await wrapper.find('.side-sub-item').trigger('keydown', { key: 'Escape', code: 'Escape' })
    await flushPromises()
    expect(wrapper.find('ul.side-sub').exists()).toBe(false)
    expect(toggleOf(wrapper, '决议').attributes('aria-expanded')).toBe('false')
    expect(document.activeElement).toBe(toggleOf(wrapper, '决议').element)
    wrapper.unmount()
  })

  it('TC-INT-812 / AC-211-01：非业委会成员菜单——不渲染报销/备用金、收入表、待办（不是置灰）', async () => {
    const { wrapper } = await mountNav('/', { menu: visibleMenu(PORTAL_MENU, { isCommittee: false }) })
    const text = wrapper.text()
    for (const t of ['报销/备用金', '收入表', '待办']) expect(text).not.toContain(t)
    expect(wrapper.findAll('.side-item')).toHaveLength(6)
    expect(wrapper.findAll('[disabled]')).toHaveLength(0)
    wrapper.unmount()
  })

  it('TC-INT-813 / AC-224-01、AC-225-01、AC-225-04：管理端菜单 9 项；账号展开恰 2 项，刷新停留 /admin/users/registered 时"账号"自动展开并高亮"注册用户"', async () => {
    const { wrapper } = await mountNav('/admin/registry', { menu: ADMIN_MENU, props: { ariaLabel: '管理端导航' } })
    expect(wrapper.attributes('aria-label')).toBe('管理端导航')
    expect(wrapper.findAll('.side-item')).toHaveLength(9)
    expect(wrapper.findAll('ul.side-sub')).toHaveLength(0)
    await toggleOf(wrapper, '账号').trigger('click')
    expect(wrapper.findAll('.side-sub-item').map((a) => a.find('.side-label').text())).toEqual(['管理员账号', '注册用户'])
    await toggleOf(wrapper, '账号').trigger('click')
    expect(wrapper.findAll('ul.side-sub')).toHaveLength(0)
    wrapper.unmount()
    const reloaded = await mountNav('/admin/users/registered', { menu: ADMIN_MENU })
    expect(toggleOf(reloaded.wrapper, '账号').attributes('aria-expanded')).toBe('true')
    expect(reloaded.wrapper.find('.side-sub-item.is-active').text()).toContain('注册用户')
    expect(toggleOf(reloaded.wrapper, '财务').attributes('aria-expanded')).toBe('false')
    reloaded.wrapper.unmount()
  })

  it('TC-INT-814 / AC-225-02、AC-224-02：内容管理展开恰 7 项；编辑页 /admin/content/posts/12 高亮"信息公开"二级项且仅此一项', async () => {
    const { wrapper } = await mountNav('/admin/content/posts/12', { menu: ADMIN_MENU })
    expect(wrapper.findAll('.side-sub-item')).toHaveLength(7)
    const active = wrapper.findAll('.side-sub-item.is-active')
    expect(active).toHaveLength(1)
    expect(active[0].find('.side-label').text()).toBe('信息公开')
    wrapper.unmount()
  })

  it('TC-INT-815 / 无障碍：aria-label 缺省为"主导航"；导航根为 nav.side-nav', async () => {
    const { wrapper } = await mountNav('/')
    expect(wrapper.element.tagName).toBe('NAV')
    expect(wrapper.classes()).toContain('side-nav')
    expect(wrapper.attributes('aria-label')).toBe('主导航')
    wrapper.unmount()
  })
})

describe('SubNavBar 窄屏二级切换条（US-230）', () => {
  async function mountBar(path, items, badges) {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/:pathMatch(.*)*', component: { template: '<i />' } }]
    })
    router.push(path)
    await router.isReady()
    const wrapper = mount(SubNavBar, { props: { items, badges }, global: { plugins: [router] } })
    await flushPromises()
    return { wrapper, router }
  }
  const units = PORTAL_MENU.find((n) => n.key === 'units').children

  it('TC-INT-816 / AC-299-04、AC-304-01：/units/appeal 切换条含 3 项（我的身份与房屋/我的认证与申述/我的同住人申请）且“我的认证与申述”高亮（aria-current=page）', async () => {
    const { wrapper } = await mountBar('/units/appeal', units, {})
    expect(wrapper.attributes('aria-label')).toBe('分区切换')
    expect(wrapper.findAll('a.sub-nav-item').map((a) => a.text())).toEqual(
      ['我的身份与房屋', '我的认证与申述', '我的同住人申请']
    )
    expect(wrapper.text()).not.toContain('选择房屋')
    const active = wrapper.findAll('.sub-nav-item.is-active')
    expect(active).toHaveLength(1)
    expect(active[0].text()).toBe('我的认证与申述')
    expect(active[0].attributes('aria-current')).toBe('page')
    wrapper.unmount()
  })

  it('TC-INT-817 / AC-230-02：决议 3 项、报销 2 项；切换路径后高亮跟随', async () => {
    const res = PORTAL_MENU.find((n) => n.key === 'resolutions').children
    const { wrapper, router } = await mountBar('/resolutions', res, {})
    expect(wrapper.findAll('.sub-nav-item')).toHaveLength(3)
    expect(wrapper.find('.sub-nav-item.is-active').text()).toBe('公开决议')
    await router.push('/resolutions/todo')
    await flushPromises()
    expect(wrapper.find('.sub-nav-item.is-active').text()).toBe('待我表决')
    wrapper.unmount()
    const claims = PORTAL_MENU.find((n) => n.key === 'claims').children
    const bar = await mountBar('/claims/todo', claims, {})
    expect(bar.wrapper.findAll('.sub-nav-item').map((a) => a.text())).toEqual(['我提交的', '待我审批'])
    bar.wrapper.unmount()
  })

  it('TC-INT-818 / AC-235-01（旧 AC-230-04）：待审批角标 2 显示在"我的身份与房屋"项且该项高亮；为 0 不显示', async () => {
    // 改写：旧在 /units/review 的"待我审批"项 → 新在 /units 的"我的身份与房屋"项
    const { wrapper } = await mountBar('/units', units, { pendingReview: 2 })
    const item = wrapper.findAll('.sub-nav-item').find((a) => a.text().includes('我的身份与房屋'))
    expect(item.classes()).toContain('is-active')
    expect(item.find('.side-badge').text()).toBe('2')
    await wrapper.setProps({ badges: { pendingReview: 0 } })
    expect(wrapper.findAll('.side-badge')).toHaveLength(0)
    wrapper.unmount()
  })

  it('TC-INT-819 / AC-215-04：详情页（不在切换条地址内）没有任何高亮项', async () => {
    const res = PORTAL_MENU.find((n) => n.key === 'resolutions').children
    const { wrapper } = await mountBar('/resolutions/12', res, {})
    expect(wrapper.findAll('.sub-nav-item.is-active')).toHaveLength(0)
    wrapper.unmount()
  })
})
