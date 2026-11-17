<!-- MOD-128：赛博终端版配图。终端窗口 + 等宽命令行 + 扫描线与 CRT 网格 + 方块光标 + 数据雨字符流 -->
<template>
  <svg class="terminal-art" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice" role="presentation" focusable="false">
    <defs>
      <pattern id="art-scan" width="8" height="4" patternUnits="userSpaceOnUse">
        <rect width="8" height="1" class="scan-line" />
      </pattern>
      <pattern id="art-crt" width="40" height="40" patternUnits="userSpaceOnUse">
        <path d="M40 0H0V40" class="crt-line" />
      </pattern>
    </defs>
    <rect class="bg" width="800" height="600" />
    <rect width="800" height="600" fill="url(#art-crt)" />
    <!-- 装饰字符一律经 CSS 伪元素输出，不进入文本内容（三套风格的页面文本须一致） -->
    <g class="rain">
      <foreignObject v-for="c in rain" :key="c.id" :x="c.x" y="10" width="40" height="580">
        <div class="rain-col" :data-t="c.text"></div>
      </foreignObject>
    </g>
    <g class="window">
      <rect class="frame" x="110" y="150" width="580" height="300" />
      <rect class="titlebar" x="110" y="150" width="580" height="38" />
      <circle class="dot dot-a" cx="136" cy="169" r="6" />
      <circle class="dot dot-b" cx="158" cy="169" r="6" />
      <circle class="dot dot-c" cx="180" cy="169" r="6" />
      <foreignObject x="200" y="155" width="470" height="30">
        <div class="title-text" data-t="cyber@hongfengling"></div>
      </foreignObject>
      <foreignObject x="140" y="205" width="520" height="150">
        <div class="cmd" data-t="> boot cyber@hongfengling"></div>
        <div class="cmd" data-t="> auth --mode secure"></div>
        <div class="cmd cmd-dim" data-t="> link established ... ok"></div>
      </foreignObject>
      <rect class="cursor" x="140" y="362" width="16" height="28" />
    </g>
    <rect width="800" height="600" fill="url(#art-scan)" />
  </svg>
</template>

<script setup>
// 数据雨：两列静态二进制字符（减少性能压力）；竖排由 CSS 的 word-break 逐字换行实现
const rain = [40, 720].map((x, k) => ({
  id: k, x, text: Array.from({ length: 22 }, (_, i) => ((i * 7 + k * 3) % 5 < 2 ? '1' : '0')).join('')
}))
</script>

<style scoped>
.terminal-art { display: block; width: 100%; height: 100%; }
.bg { fill: var(--bg); }
.scan-line { fill: var(--accent); opacity: 0.07; }
.crt-line { fill: none; stroke: var(--accent); stroke-width: 1; opacity: 0.08; }
.rain-col { width: 40px; word-break: break-all; line-height: 26px; opacity: 0.35; }
.rain-col::before { content: attr(data-t); font-family: var(--mono); font-size: 20px; color: var(--accent); }
.frame { fill: var(--surface); stroke: var(--accent); stroke-width: 2; filter: drop-shadow(0 0 10px var(--accent)); }
.titlebar { fill: var(--glass); stroke: var(--accent); stroke-width: 1; }
.dot-a { fill: var(--accent); }
.dot-b { fill: var(--accent-2); }
.dot-c { fill: var(--muted); }
.title-text::before { content: attr(data-t); font-family: var(--mono); font-size: 16px; font-weight: 700; color: var(--text); }
.cmd { height: 45px; }
.cmd::before { content: attr(data-t); font-family: var(--mono); font-size: 22px; color: var(--accent); }
.cmd-dim::before { color: var(--muted); }
.cursor { fill: var(--accent); animation: term-blink 1s steps(1) infinite; }
@keyframes term-blink { 50% { opacity: 0; } }
:global(html[data-perf="low"]) .cursor { animation: none; }
</style>
