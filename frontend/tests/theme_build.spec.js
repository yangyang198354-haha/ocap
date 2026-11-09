// MOD-027：风格构建与对比度守护（REQ-NFUNC-005；AC-088-01、AC-080-03）
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { loadThemeFiles, run } from '../../scripts/themes/build.mjs'
import { contrastRatio } from '../../scripts/themes/schema.mjs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..')
const entries = loadThemeFiles(path.join(ROOT, 'themes'))

describe('风格生成物与源一致', () => {
  it('themes/ 三份定义全部合规，且已提交的生成物与重新生成的内容一致', () => {
    const { outputs, errors, fatal } = run(path.join(ROOT, 'themes'))
    expect(fatal).toBeNull()
    expect(errors).toEqual([])
    for (const [rel, content] of Object.entries(outputs)) {
      expect(fs.readFileSync(path.join(ROOT, rel), 'utf8'), rel).toBe(content)
    }
  })
})

// design_spec §5 表内数值（A 的渐变取最暗端 5.13）
const FLOOR = {
  neon: { '正文 / 玻璃卡片（最坏情况）': 12.92, '次要文字 / 玻璃卡片': 6.41, '强调文字 / 玻璃卡片': 6.04, '主按钮白字 / 渐变最暗端': 5.13 },
  bento: { '正文 / 白卡': 18.66, '次要文字 / 白卡': 5.95, '强调色 / 白卡': 6.29, 'Hero 白字 / 渐变亮端': 4.6 },
  terminal: { '正文 / 面板': 16.83, '次要文字 / 面板': 6.67, '荧光绿 / 面板': 15.96, '按钮黑字 / 荧光绿': 16.75 }
}

describe('对比度（AC-088-01）', () => {
  for (const { def } of entries) {
    it(`${def.key}：每个组合实测不低于声明阈值，且 ≥ 4.5`, () => {
      for (const c of def.contrast) {
        const ratio = contrastRatio(def.tokens[c.fg] || c.fg, c.bg)
        expect(ratio, c.label).toBeGreaterThanOrEqual(c.min)
        expect(c.min).toBeGreaterThanOrEqual(4.5)
      }
    })
    it(`${def.key}：design_spec §5 的 4 个组合不低于表内值（四舍五入到两位）`, () => {
      for (const [label, floor] of Object.entries(FLOOR[def.key])) {
        const c = def.contrast.find((x) => x.label === label)
        expect(c, label).toBeTruthy()
        const ratio = contrastRatio(def.tokens[c.fg] || c.fg, c.bg)
        expect(Math.round(ratio * 100) / 100, label).toBeGreaterThanOrEqual(floor)
      }
    })
  }
})
