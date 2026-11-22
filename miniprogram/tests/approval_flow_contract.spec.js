// GROUP_D 契约测试（ocap_approval_flow）：小程序调用路径与后端路由、三端文案一致。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const read = (rel) => fs.readFileSync(path.join(ROOT, rel), 'utf8')

describe('小程序审批契约（US-320 / AC-331-01、AC-331-02）', () => {
  it('TC-INT-1310 / AC-331-01：api.js 暴露任务、决策（含备注）与时间线接口', () => {
    const src = read('utils/api.js')
    expect(src).toContain("'/approval/tasks'")
    expect(src).toContain('/approval/instances/${instanceId}/decision')
    expect(src).toContain('comment')
    expect(src).toContain('/approval/instances/${instanceId}')
  })

  it('TC-INT-1311 / AC-331-02：审批页面已注册且引用统一文案', () => {
    const pages = JSON.parse(read('pages.json'))
    const paths = pages.pages.map((p) => p.path)
    expect(paths).toContain('pages/approvals/index')
    expect(paths).toContain('pages/approvals/detail')
    const detail = read('pages/approvals/detail.vue')
    expect(detail).toContain('STEP_STRATEGY_LABELS')
    expect(detail).toContain('APPROVAL_ACTION_LABELS')
    expect(detail).toContain('APPROVAL_STATUS_LABELS')
    const index = read('pages/approvals/index.vue')
    expect(index).toContain('step_name')
  })

  it('TC-UNIT-1312 / AC-328-01：三端步骤策略/状态文案取值一致', () => {
    const web = read(path.join('..', 'frontend', 'src', 'shared', 'labels.js'))
    const mini = read('utils/labels.js')
    for (const name of ['STEP_STRATEGY_LABELS', 'STEP_STATUS_LABELS', 'APPROVAL_ACTION_LABELS', 'APPROVAL_STATUS_LABELS']) {
      const pick = (src) => src.slice(src.indexOf(`export const ${name}`)).split('\n')[0].replace(/\r/g, '')
      expect(pick(mini)).toBe(pick(web))
    }
  })
})
