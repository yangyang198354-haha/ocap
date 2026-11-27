import fs from 'node:fs'
import { URL } from 'node:url'
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { ElButton } from 'element-plus'
import postcss from 'postcss'
import { contrastRatio, mix } from '../../scripts/themes/schema.mjs'

const read = (path) => fs.readFileSync(new URL(path, import.meta.url), 'utf8')
const buttons = postcss.parse(read('../src/shared/buttons.css'))
const generated = postcss.parse(read('../src/theme/generated/themes.css'))
const theme = (name) => JSON.parse(read(`../../themes/${name}.theme.json`)).tokens
const rule = (root, selector) => root.nodes.find((node) => node.type === 'rule' && node.selector === selector)
const value = (node, property) => node?.nodes.find((item) => item.type === 'decl' && item.prop === property)?.value
const scope = 'html[data-theme] .el-button'

describe('Web button design system', () => {
  it('uses one stylesheet after theme and login styles, with no generated surface-dependent primary color', () => {
    const main = read('../src/main.js')
    expect(main.indexOf('./shared/buttons.css')).toBeGreaterThan(main.indexOf('./brand/auth-motion.css'))
    expect(generated.toString()).not.toMatch(/\.el-button--primary\s*\{/)
    expect(value(rule(buttons, 'html[data-theme="bento"]'), '--button-primary-fill')).toBe('var(--accent)')
    expect(value(rule(buttons, 'html[data-theme]'), '--button-primary-fill')).toBe('var(--accent-bg)')
    expect(value(rule(buttons, scope), 'border-radius')).toBe('var(--radius-btn)')
    expect(value(rule(buttons, scope), 'font-family')).toBe('var(--font)')
  })

  it('separates primary, secondary, text, approval, and destructive actions', () => {
    expect(value(rule(buttons, scope), '--button-fill')).toBe('var(--surface)')
    expect(value(rule(buttons, scope + '--primary:not(.is-link, .is-text, .is-plain)'), '--button-fill')).toBe('var(--button-primary-fill)')
    expect(value(rule(buttons, scope + ':is(.is-link, .is-text)'), '--button-fill')).toBe('transparent')
    expect(value(rule(buttons, scope + '--success'), '--button-ink')).toBe('var(--success)')
    expect(value(rule(buttons, scope + '--danger'), '--button-border')).toBe('var(--danger)')
    const finalAction = buttons.nodes.find((node) => node.selector?.includes('.button-confirm-danger'))
    expect(value(finalAction, '--button-fill')).toBe('var(--button-danger-fill)')
    expect(read('../src/shared/confirm.js')).toContain("confirmButtonClass: 'button-confirm-danger'")
    expect(read('../src/portal/Tasks.vue')).toContain("pendingAction === 'APPROVE' ? '确认通过' : '确认拒绝'")
    expect(read('../src/portal/units/UnitsReview.vue')).toContain('type="success"')
  })

  it('defines 44px regular, 36px compact PC table and 52px auth sizes with a visible focus ring', () => {
    expect(read('../src/shared/style.css')).toContain('--hit-min: 44px')
    expect(value(rule(buttons, scope), '--button-height')).toBe('var(--hit-min)')
    expect(value(rule(buttons, scope), '--button-font-size')).toBe('14px')
    const desktop = buttons.nodes.find((node) => node.name === 'media' && node.params === '(min-width: 768px)')
    const compact = rule(desktop, 'html[data-theme] .admin-shell .el-table .el-button')
    expect(value(compact, '--button-height')).toBe('36px')
    expect(value(compact, '--button-font-size')).toBe('13px')
    const auth = rule(buttons, 'html[data-theme] .auth-shell .el-button--primary:not(.is-link, .is-text, .is-plain)')
    expect(value(auth, '--button-height')).toBe('52px')
    expect(value(auth, '--button-font-size')).toBe('16px')
    const mobile = buttons.nodes.find((node) => node.name === 'media' && node.params === '(max-width: 767.98px)')
    expect(value(rule(mobile, scope), 'min-width')).toBe('var(--hit-min)')
    const focus = buttons.nodes.find((node) => node.selector?.startsWith(scope + ':focus-visible'))
    expect(value(focus, 'outline')).toBe('2px solid var(--button-focus)')
  })

  it('keeps existing accessible button text in loading state and blocks interaction when disabled', async () => {
    const wrapper = mount(ElButton, { props: { type: 'primary' }, slots: { default: '保存' } })
    await wrapper.setProps({ loading: true })
    const spinner = rule(buttons, scope + '.is-loading > .el-icon.is-loading')
    expect(value(spinner, 'position')).toBe('absolute')
    expect(wrapper.find('.el-icon.is-loading').exists()).toBe(true)
    expect(wrapper.text()).toBe('保存')
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeUndefined()
    await wrapper.setProps({ loading: false, disabled: true })
    expect(wrapper.element.disabled).toBe(true)
    expect(generated.toString()).toMatch(/prefers-reduced-motion: reduce[\s\S]*transition: none !important/)
    wrapper.unmount()
  })

  it('keeps primary and destructive button foreground contrast across themes', () => {
    for (const name of ['bento', 'terminal', 'neon']) {
      const tokens = theme(name)
      const fill = name === 'bento' ? tokens.accent : tokens.accentBg
      const colors = fill.startsWith('linear-gradient') ? fill.match(/#[0-9a-f]{6}/gi) : [fill]
      for (let i = 0; i < colors.length; i++) {
        const next = colors[i + 1] ?? colors[i]
        for (let n = 0; n <= 20; n++) {
          expect(contrastRatio(tokens.onAccent, mix(colors[i], next, n / 20))).toBeGreaterThan(4.5)
        }
      }
      if (name === 'bento') {
        expect(contrastRatio(tokens.onAccent, mix(tokens.accent, '#ffffff', 0.07))).toBeGreaterThan(4.5)
      }
      const dangerFill = name === 'neon' ? value(rule(buttons, 'html[data-theme="neon"]'), '--button-danger-fill') : tokens.danger
      expect(contrastRatio(tokens.onAccent, dangerFill)).toBeGreaterThan(4.5)
    }
  })
})
