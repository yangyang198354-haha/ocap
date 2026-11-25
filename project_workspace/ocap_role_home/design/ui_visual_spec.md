<file_header>
  <author_agent>ui-design-spec</author_agent>
  <timestamp>2026-11-25T15:05:00+08:00</timestamp>
  <project_name>ocap_role_home</project_name>
  <version>1.0.0</version>
  <input_files>
    <file>frontend/src/shared/style.css</file>
    <file>frontend/src/portal/Home.vue</file>
    <file>frontend/src/portal/Resolutions.vue</file>
    <file>frontend/src/portal/Polls.vue</file>
    <file>frontend/src/portal/Reports.vue</file>
    <file>frontend/src/portal/Info.vue</file>
    <file>miniprogram/App.vue</file>
    <file>miniprogram/pages/index/index.vue</file>
    <file>themes/bento.theme.json</file>
    <file>themes/neon.theme.json</file>
    <file>themes/terminal.theme.json</file>
    <file>scripts/themes/build.mjs</file>
  </input_files>
  <phase>UI_SPEC</phase>
  <status>APPROVED</status>
</file_header>

# 角色化首页 UI 规范（Web + 小程序）

## 0. 决策摘要

- 目标：解决“页面单调、卡片无边界、右侧链接贴边、管理快捷卡中卡、内页无风格、动效弱”。
- 范围：视觉层与微交互；**不改**模块顺序、模块可见性、接口、权限、路由、数据口径（与已交付的 `ocap_role_home` 行为一致）。
- 三主题：极光 Bento（浅色）、霓虹玻璃（深色）、赛博终端（深色）。
- 两端：Web 与微信小程序共用同一套令牌名与模块 key；单位按 `1px = 2rpx` 映射。
- 约束：不新增依赖、不引入图片素材、不使用容器；小程序不用 `backdrop-filter`，不做长循环动画。
- 本文件为评审稿（C 方案），评审通过后再改代码。

## 1. 设计原则

1. **边界先于装饰**：每张卡必须有可辨认的 1px 描边或等效阴影，白卡叠白底时靠描边与顶部高光分层。
2. **一屏一个焦点**：每屏只允许一个高饱和区域（Hero 或主 CTA），其余用 accent 10% 以内的淡染。
3. **光学对齐**：文字与链接按卡片内容盒对齐，右侧链接离圆角至少 12px，不用“贴边文字”。
4. **信息三层**：标题（16/650）→ 主数据（28–40/700 等宽）→ 辅助（12–13 muted）；数量只在标题出现一次。
5. **动效服务层级**：进入用位移+透明度，交互用 150–220ms；不做无意义的循环动画。
6. **主题是同一骨架的不同材质**：三主题只改材质、圆角、光效与字体细节，不改布局与模块顺序。

## 2. 设计令牌

### 2.1 间距与尺寸（Web px / 小程序 rpx）

| 令牌 | Web | 小程序 | 用途 |
|---|---|---|---|
| `--space-1` | 4 | 8 | 图标与文字微间距 |
| `--space-2` | 8 | 16 | 行内间距 |
| `--space-3` | 12 | 24 | 卡片内元素间距 |
| `--space-4` | 16 | 32 | 移动端卡片内边距 |
| `--space-5` | 20 | 40 | 紧凑卡片内边距 |
| `--space-6` | 24 | 48 | 桌面卡片内边距 |
| `--space-8` | 32 | 64 | 页面区块间距 |
| `--card-gap` | 16/20 | 24 | 网格间距（移动/桌面） |
| `--hit-min` | 44 | 88 | 最小点击区（保持现状） |
| `--link-h` | 32 | 64 | 右上 ghost 链接高度 |

### 2.2 新增令牌（写入 `themes/*.theme.json`，再生成两端产物）

| 令牌 | Bento | Neon | Terminal | 用途 |
|---|---|---|---|---|
| `borderStrong` | `#D8DBE8` | `rgba(255,255,255,.18)` | `#3A3A40` | hover/选中描边 |
| `surfaceTint` | `#F8F9FD` | `rgba(255,255,255,.06)` | `#16161A` | 列表行/动作块 hover 底 |
| `shadowRest` | `0 1px 2px rgba(17,18,26,.04), 0 8px 24px -12px rgba(49,46,129,.12)` | `0 0 0 1px rgba(255,255,255,.10), 0 0 32px -12px rgba(124,92,255,.35)` | `0 0 0 1px #26262A` | 卡片静息 |
| `shadowHover` | `0 2px 4px rgba(17,18,26,.05), 0 18px 44px -16px rgba(49,46,129,.22)` | `0 0 0 1px rgba(169,150,255,.45), 0 0 48px -10px rgba(34,211,238,.35)` | `0 0 0 1px #C6FF3D, 0 0 24px -8px rgba(198,255,61,.35)` | 卡片 hover |
| `insetHighlight` | `inset 0 1px 0 rgba(255,255,255,.8)` | `inset 0 1px 0 rgba(255,255,255,.12)` | `none` | 顶部高光 |
| `heroPad` | `28px` | `28px` | `24px` | Hero 内边距 |
| `cardRadius` | `28px` | `20px` | `4px` | 保持现有半径令牌 |
| `motionBase` | `220ms` | `220ms` | `160ms` | 交互时长 |
| `motionEase` | `cubic-bezier(.2,.7,.2,1)` | 同左 | `cubic-bezier(.2,.8,.2,1)` | 缓动 |

> 不修改现有 `bg/surface/text/muted/line/accent` 等颜色值，避免破坏 `themes` 的 contrast 校验；只新增材质与动效令牌。

### 2.3 字体层级

| 角色 | 字号/行高 | 字重 | 备注 |
|---|---|---|---|
| 页面标题 | 24/32（MP 48/64rpx） | 700 | 内页 `.page-head h1` |
| 卡片标题 | 16/24 | 650 | 现有 `.title` |
| 主数据 | 34–40/44 | 700，等宽 | 财务合计 |
| 正文 | 14/22 | 400 | — |
| 辅助 | 12–13/18 | 400，muted | 来源、时间、说明 |
| 标签 | 11–12/16 | 500，字距 .04em | 编号、状态 |

## 3. 布局与栅格

- Web：`--content-pad` 保持 `clamp(12px, 1.2vw, 32px)`；`.page` 内容最大宽度 1180px。
- 首页：`<768px` 单列；`≥768px` 4 栏 `.home-grid`；`home-half` 占 2 栏，`home-full` 占 4 栏（保持现状）。
- 卡片间距：移动 12px，桌面 20px；模块之间不再额外 `margin-bottom`。
- 卡片内边距：移动 16px，桌面 24px；Hero 28px。
- 右侧链接必须离卡片右边 12px 以上：`.card-head` 使用 `padding-right: 4px`，`.link` 自身有 10px 内边距。
- 小程序：单列；卡片 32rpx 内边距；模块间距 24rpx；底部 Tab 不变。

## 4. 卡片系统

统一使用 `.card`，通过变体类叠加；**不新增嵌套卡片**。

| 变体 | 类名 | 用途 | 结构 |
|---|---|---|---|
| Feature | `.card.is-feature` | Hero 欢迎卡 | 问候 + 身份 + 1 个主 CTA + 背景光效 |
| Data | `.card.is-data` | 财务公开、房屋、待我处理 | 图标 + 标题 + 主数据 + 辅助行 + ghost 链接 |
| List | `.card.is-list` | 投票、决议、信息、待办 | 标题 + 数量胶囊 + 列表行 + 空态 |
| Action | `.card.is-action` | 管理快捷 | 标题 + 3 个无边框动作块 |
| Plain | `.card` | 其他内页 | 仅材质与描边 |

### 4.1 卡片材质规则

- 通用：`background: var(--surface); border: 1px solid var(--line); border-radius: var(--card-radius); box-shadow: var(--inset-highlight), var(--shadow-rest); padding: var(--card-pad);`
- Hover（Web）：`translateY(-3px)` + `shadow-hover` + `border-color: borderStrong`；`transition: 220ms var(--motion-ease)`。
- 小程序：无 hover，使用 `hover-class="is-pressed"`，按下时 `background: var(--surface-tint)`，不做位移。
- 禁止：卡片内部再出现带 1px 边框的同级子卡；子元素用底色或分隔线表达分组。

### 4.2 卡片头部

```
[图标 32×32]  标题 16/650   [数量胶囊]              [ghost 链接 32h]
```
- 图标块：32px，`background: var(--glass)`，`border-radius: var(--radius-sm)`，图标 18px，颜色 `--accent-text`。
- 数量胶囊：`padding: 2px 8px; border-radius: 999px; background: var(--glass); font-size: 12px; color: var(--muted)`。
- Ghost 链接：`height: 32px; padding: 0 10px; border-radius: 999px; font-size: 13px;` 默认透明，hover `background: var(--glass)`；箭头 `→` 在 hover 时右移 2px。

### 4.3 空态

- 最小高度 112px（MP 224rpx），居中：32px 图标 + 13px 文案 + 文字 CTA。
- 文案示例：“暂无进行中的投票” + “去投票 →”；不允许整卡半屏空白。
- 内容类空态保留；任务类 0 仍然整卡隐藏（不改变 C-397/AC-359-03）。

## 5. 首页逐模块规范

### 5.1 Hero 欢迎卡

- 内边距 28px；标题 24/30（桌面 30/38）；身份行 13px，透明度 .85。
- 背景：Bento 现有三色渐变；Neon 渐变 + 右上 160px 青色光斑；Terminal 纯深底 + 扫描线 + 左侧 4px 荧光绿竖条。
- 动效：背景位移 24s 循环（Terminal 关闭）；进入时标题淡入上移 8px。
- 不显示手机号、不显示重复计数徽章（保持已交付行为）。

### 5.2 我的房屋 / 待我处理（Data 卡）

- 布局：图标 + 标题 + 主数字（28/700）+ 辅助行 + 右上 ghost 链接。
- 主数字：`我的房屋 · 2` 的 `2` 用 accent 色；`待我处理 · 1` 的 `1` 用 warning 色。
- 链接文案保持“房屋明细”“去处理”，但改为 ghost 按钮。
- 两卡在桌面各占 2 栏，等高；内容不足时用 `justify-content: space-between` 撑开，不留大片空白。

### 5.3 财务公开（Data 卡）

- 合计：34/40 等宽，`letter-spacing: -.02em`；下方两个 chip：“N 个账户”“本月收支”，不要只放一串数字。
- 账户行：`padding: 10px 0`，hover/tap 背景 `surfaceTint`；名称左、金额右，金额等宽。
- 报表入口：ghost 按钮“财务报表”。
- 游客只显示合计 + 报表入口（保持 D-RH-03）。

### 5.4 管理快捷（Action 卡，去掉卡中卡）

推荐结构：3 个**无边框动作块**横排（移动端可 3 列压缩或纵向 3 行）：

```
[40px 圆形图标]  收入表
                 查看与登记
                          →
```

- 动作块：`padding: 12px; border: 0; border-radius: var(--radius-md); background: transparent;`
- hover/按下：`background: var(--surface-tint)`。
- 图标：40px 圆，`background: var(--glass)`，图标 20px，accent 色。
- 文案：主 14/600，副 12 muted；右侧箭头 16px。
- 块之间用 `gap: 12px`，不用边框或竖线。
- 小程序副文案可省略，仅保留“图标 + 主文案 + 箭头”，避免拥挤。

### 5.5 投票与调查 / 公开决议 / 信息公开（List 卡）

- 头部：图标 + 标题 + 数量胶囊 + “查看全部”ghost 链接。
- 列表行：`min-height: 56px; padding: 12px 0; border-top: 1px solid var(--line)`；首行无上边框。
- 决议行：`R-0031` 编号 chip + 标题 + 状态 tag + 来源 tag（业委会 accent / 业主代表 accent2）+ 行尾箭头。
- 投票行：标题 + 截止时间 + 状态 tag；截止 24h 内加 6px 呼吸圆点。
- 信息行：标题 + 发布时间 + 摘要一行（可选）。
- 空态按 §4.3。

## 6. 内页统一页面壳

所有内页（决议、投票/调查、财务/报表、信息、我的）新增同一结构：

```
.page-head
  .page-eyebrow    12/500 uppercase accent（如 “RESOLUTIONS”）
  h1               24/700
  .page-desc       13 muted
  .page-actions    ghost/主按钮
.section
  .section-head    标题 + 数量 + 右侧动作
  .card ...        列表或数据
```

- `.page-head`：`padding: 4px 0 16px`，底部 1px `--line`（可无），与首卡间距 16px。
- 筛选/分段控件：放入 `.toolbar`（`display:flex; gap:8px; flex-wrap:wrap`），不要直接塞进卡片头部。
- 内页卡片默认 `is-list` 或 `is-data`；详情页用 `Plain` + 顶部返回链接。
- 侧栏（Web）：选中态 `background: color-mix(in srgb, var(--accent) 10%, transparent)` + 左侧 3px accent 竖条 + accent 文字；hover 用 `surfaceTint`；不再用纯黑胶囊。
- 小程序：无侧栏；页面顶部用 `.page-head`，底部 Tab 保持现状。

## 7. Web 与小程序映射

| 项 | Web | 小程序 |
|---|---|---|
| 单位 | px | rpx（1px = 2rpx） |
| 布局 | 4 栏 Bento | 单列卡片流 |
| 交互态 | hover + focus-visible | `hover-class` 按下态，无 hover |
| 材质 | 支持 `backdrop-filter` | 不使用；用 `--glass-low-end` 实底回退 |
| 颜色计算 | 可用 `color-mix` | 不用；令牌在生成时预计算 |
| 动效 | CSS + 可选 JS 数字滚动 | 仅 transform/opacity；不做背景长循环 |
| 模块顺序 | 与已交付一致 | 同名同序 |
| 主题切换 | `html[data-theme]` | `.theme-{key}` 根类 |

## 8. 动效规范

| 令牌/场景 | 时长 | 缓动 | 触发 | 备注 |
|---|---|---|---|---|
| `motion-fast` | 150ms | ease-out | 链接、箭头、tag | 只改颜色/位移 2px |
| `motion-base` | 220ms | `cubic-bezier(.2,.7,.2,1)` | 卡片 hover、按钮 | 位移 ≤3px |
| `motion-slow` | 320ms | 同上 | 卡片进入、页面切换 | 位移 8–12px |
| 卡片错峰 | 55ms/张 | — | 首屏进入 | 最多 6 张，总时长 ≤400ms |
| 财务数字 | 320ms | ease-out | 数据到达 | `requestAnimationFrame`，从 0 到目标值 |
| Hero 背景 | 24s | linear | 常驻 | 仅 Bento/Neon；Terminal 关闭 |
| 截止呼吸 | 1.6s | ease-in-out | <24h 投票 | 圆点透明度 .35→1 |

统一：

```css
@keyframes card-rise {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; transition: none !important; }
}
```

小程序不提供可靠的 `prefers-reduced-motion`，因此只保留一次性进入动画与按下态，不做常驻循环（Hero 背景除外，可用静态渐变）。

## 9. 可访问性与对比度

- 正文对比度 ≥ 4.5:1，大字 ≥ 3:1；沿用 `themes/*.theme.json` 的 `contrast` 表，新增令牌不改变文字色。
- `:focus-visible` 保持 2px accent 外环 + 2px offset；ghost 链接的点击区高度 ≥32px（桌面）/64rpx（小程序）。
- 颜色不是唯一信息载体：状态同时用文字 tag；来源标签除颜色外带文字。
- 动效不得导致布局抖动；所有 hover 位移不影响相邻卡片位置（使用 transform）。

## 10. 页面级改造清单

### P0（首页观感，优先）

| 文件 | 改动 |
|---|---|
| `frontend/src/shared/style.css` | `.card` 内边距/阴影/顶部高光；`.card-head` 与 `.link` ghost 按钮；空态压缩；`card-rise` 与 hover 过渡 |
| `frontend/src/portal/Home.vue` | Hero 内边距；Data 卡图标/主数字；管理快捷改 3 个无边框动作块；列表行与来源 tag；空态 CTA |
| `miniprogram/App.vue` | 与上对应的 rpx 样式；`.card` 材质、ghost 链接、动作块、空态 |
| `miniprogram/pages/index/index.vue` | 管理快捷结构；图标/数字/来源 tag；按下态 |
| `themes/*.theme.json` + 生成脚本 | 新增 §2.2 令牌；`node scripts/themes/build.mjs` 重新生成 Web/MP 产物 |

### P1（内页统一）

| 文件 | 改动 |
|---|---|
| `frontend/src/shared/style.css` | `.page-head`、`.section`、`.toolbar`、列表行、侧栏选中态 |
| `frontend/src/portal/{Resolutions,Polls,Reports,Info,Me}.vue` | 套用页面壳与卡片变体 |
| `themes/*.web.css` / `*.mp.css` | 三主题背景层与主题特有细节（光斑、网格、扫描线、卡片描边） |
| 小程序对应页面 | `.page-head`、卡片变体、空态 |

### P2（点睛）

| 文件 | 改动 |
|---|---|
| `frontend/src/portal/Home.vue` | 财务数字滚动；截止呼吸 |
| 主题 CSS | Hero 背景缓慢位移（Bento/Neon） |
| 小程序首页 | 仅保留一次性进入动画 |

## 11. 验收清单

- [ ] 三主题 × 五角色（游客、同住人、业主、代表、委员）首页逐屏截图核对；模块顺序与已交付版本一致。
- [ ] 卡片均有可见边界；右侧链接离卡片右边 ≥12px；无文字贴边。
- [ ] 管理快捷不再出现“卡中卡”；3 个动作块在 375px 与 1280px 下均不溢出。
- [ ] 空态高度 ≤120px，且带 CTA；任务类 0 仍然隐藏。
- [ ] 内页均有统一 `.page-head`，不再是“纯白卡片堆”。
- [ ] 动效：进入错峰、hover 上移、链接箭头位移；开启 reduced motion 后全部关闭。
- [ ] 对比度沿用主题 `contrast` 表，无新增低对比文字。
- [ ] 构建与测试：Web `npx vitest run` + `npm run build -- --base=/ocap/`；小程序 `npm test` + `UNI_INPUT_DIR=. npx uni build -p mp-weixin`。

## 12. 风险与待确认

| 编号 | 事项 | 建议 |
|---|---|---|
| UI-Q1 | 是否允许在 `themes/*.theme.json` 新增令牌并重新生成 | 建议允许；否则只能把阴影写死在页面 CSS，三主题会更难维护 |
| UI-Q2 | 侧栏选中态是否从黑胶囊改为 accent 淡染 + 竖条 | 建议改；更贴合 Bento/Neon/Terminal |
| UI-Q3 | 内页是否全部套 `.page-head` | 建议是；这是“内页不再白板”的关键 |
| UI-Q4 | 管理快捷是否保留副文案 | Web 保留；小程序可省略，避免 3 列拥挤 |
| UI-Q5 | 是否接受 Hero 背景缓慢循环 | Bento/Neon 可；Terminal 与低性能设备建议静态 |
| UI-Q6 | 财务数字滚动是否引入 JS | 建议引入单文件 `requestAnimationFrame`，无新依赖；不做也可 |

## 13. 实施记录（2026-11-25）

已按“按推荐”落地 P0 + P1（Web 与小程序同步）；P2（财务数字滚动、截止呼吸）待下一批。

- 主题令牌：`themes/*.theme.json` 新增 `borderStrong/surfaceTint/shadowRest/shadowHover/insetHighlight/motionBase/motionEase`，`scripts/themes/build.mjs` 映射为 CSS 变量，生成物已重跑。
- Web：`.card` 内边距/描边/阴影/hover；`.card-head` 图标与 ghost 链接；`.page-head/.section-head/.toolbar`；Hero 与列表动效；管理快捷改为无边框动作块；空态加 CTA。
- 小程序：`App.vue` 卡片/页面头/动作块 rpx 样式；首页管理快捷与空态 CTA；决议/投票/信息/我的页补 `page-head`。
- Bento 侧栏选中态由黑色胶囊改为 accent 10% 淡染 + accent 文字（`themes/bento.web.css`）。
- 验证：Web `58 files / 613 tests passed`，构建 `✓ built in 14.16s`；小程序 `23 files / 157 tests passed`，`DONE Build complete.`；主题 `--strict --check` 退出码 0。
- 未改动：模块顺序/可见性、接口、权限、路由、数据口径。
