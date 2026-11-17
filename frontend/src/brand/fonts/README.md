# 品牌字体 OcapBrand（ADR-123）

- 文件：`OcapBrand-subset.woff2`（12044 字节，sha256 `c02ca28cb597dce5fcf98fa3c63de4a54604aeec43b5c3021f700150a3422109`），许可证文本 `OFL.txt`（SIL OFL 1.1，随字体分发）。
- 来源：得意黑 Smiley Sans v2.0.1（Oblique），https://github.com/atelier-anchor/smiley-sans ，版权人 atelierAnchor。
- 子集字符：U+0020-007E（ASCII 可见字符）+ `红枫岭管理后台登录注册手机号·`。只用于品牌文字（`.brand-font`：品牌名、管理后台标题、登录/注册页标题）；子集外字符会回退到 `var(--font)` 系统字体。
- 改名原因：OFL 1.1 的保留字体名条款（Reserved Font Name：`Smiley`、`得意黑`）规定修改版不得使用保留名，子集化属于修改，故 name 表（nameID 1/3/4/6/16）已改为 `OcapBrand`；CSS 中只能使用 `OcapBrand`，不得出现 `Smiley`/`得意黑` 作为 font-family 名。
- 引用位置：`../brand.css` 的 `@font-face`（`font-display: swap`），Vite 构建时带哈希输出到 `dist/assets`。不使用 CDN。
- 重新生成（开发机一次性步骤，fontTools 不属于仓库依赖，字体源文件不入库）：
  1. 从上述 releases 页取 v2.0.1 的 Oblique `.ttf`（或 `.woff2`）源文件。
  2. `pyftsubset <源文件> --unicodes="U+0020-007E" --text="红枫岭管理后台登录注册手机号·" --flavor=woff2 --layout-features='*' --output-file=OcapBrand-subset.woff2`
  3. 用 fontTools 把 name 表 nameID 1/3/4/6/16 改为 `OcapBrand`（不得保留 Smiley/得意黑）。
  4. 核对 `OFL.txt` 与源包 LICENSE 一致；更新本文件的 sha256。
  新增品牌文字时需把新字符加入第 2 步的 `--text`。
