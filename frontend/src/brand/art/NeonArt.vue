<!-- MOD-128：霓虹玻璃版配图。发光紫环 + 几何红枫叶（青色电路脉络）+ 透视网格 + 漂移粒子；颜色全部取语义变量与主题样式 -->
<template>
  <svg class="neon-art" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice" role="presentation" focusable="false">
    <rect class="bg" width="800" height="600" />
    <g class="aurora">
      <ellipse class="aurora-a" cx="250" cy="120" rx="320" ry="180" />
      <ellipse class="aurora-b" cx="600" cy="90" rx="260" ry="150" />
    </g>
    <g class="grid">
      <line v-for="l in vLines" :key="`v${l.x}`" :x1="l.x1" y1="600" :x2="400" y2="330" />
      <line v-for="y in hLines" :key="`h${y}`" x1="0" :y1="y" x2="800" :y2="y" />
    </g>
    <g class="emblem" transform="translate(300 262) scale(10.4) translate(-16 -16)">
      <path class="leaf" d="M16 3.6 L18.4 8.6 L20.2 7.4 L19.8 11.4 L24.4 9.8 L22.4 13.8 L27.4 13.4 L24.2 16.6 L28.2 18.4 L23.6 19.4 L24.8 23.4 L20.6 21.6 L20.2 26.2 L17.2 23 L16 28.4 L14.8 23 L11.8 26.2 L11.4 21.6 L7.2 23.4 L8.4 19.4 L3.8 18.4 L7.8 16.6 L4.6 13.4 L9.6 13.8 L7.6 9.8 L12.2 11.4 L11.8 7.4 L13.6 8.6 Z" />
      <path class="stem" d="M16 23.2 L16 29.4" />
      <g class="traces">
        <path d="M16 23.2 L16 12.6" />
        <path d="M16 17.2 L12.4 13.6 L10.6 13.6" />
        <path d="M16 17.2 L19.6 13.6 L21.4 13.6" />
        <path d="M16 19.8 L11.2 16.4 L8.4 16.4" />
        <path d="M16 19.8 L20.8 16.4 L23.6 16.4" />
        <path d="M16 12.6 L13.6 9.8" />
        <path d="M16 12.6 L18.4 9.8" />
        <circle cx="10.6" cy="13.6" r="0.8" />
        <circle cx="21.4" cy="13.6" r="0.8" />
        <circle cx="8.4" cy="16.4" r="0.8" />
        <circle cx="23.6" cy="16.4" r="0.8" />
        <circle cx="13.6" cy="9.8" r="0.8" />
        <circle cx="18.4" cy="9.8" r="0.8" />
      </g>
    </g>
    <g class="ring">
      <circle class="ring-a" cx="300" cy="262" r="205" />
      <circle class="ring-b" cx="300" cy="262" r="232" />
    </g>
    <g class="dots">
      <circle v-for="p in particles" :key="p.id" class="particle" :cx="p.x" :cy="p.y" :r="p.r" :style="{ animationDelay: p.d + 's' }" />
    </g>
    <rect class="underline" x="80" y="520" width="200" height="3" rx="1.5" />
  </svg>
</template>

<script setup>
// 灭点 (400,330)：竖线由底边等距点收束，横线按平方间距加密，形成透视网格
const vLines = Array.from({ length: 17 }, (_, i) => ({ x: -400 + i * 100, x1: -400 + i * 100 }))
const hLines = Array.from({ length: 7 }, (_, i) => Math.round(330 + 270 * ((i + 1) / 7) ** 2))
const particles = Array.from({ length: 10 }, (_, i) => ({
  id: i, x: 90 + i * 70, y: 120 + ((i * 61) % 260), r: 1.6 + (i % 3), d: -i * 0.9
}))
</script>

<style scoped>
.neon-art { display: block; width: 100%; height: 100%; }
.bg { fill: var(--bg); }
.aurora ellipse { fill: var(--accent); opacity: 0.16; filter: blur(60px); }
.aurora-b { fill: var(--accent-2); opacity: 0.12; }
.grid line { stroke: var(--accent); stroke-width: 1; opacity: 0.28; }
.leaf { fill: var(--accent); stroke: var(--accent-2); stroke-width: 0.25; }
.stem { fill: none; stroke: var(--accent); stroke-width: 0.9; stroke-linecap: round; }
.traces { fill: none; stroke: var(--accent-2); stroke-width: 0.85; stroke-linecap: round; stroke-linejoin: round; }
.traces circle { fill: var(--accent-2); stroke: none; }
.ring circle { fill: none; }
.ring-a { stroke: var(--accent); stroke-width: 2; opacity: 0.85; filter: drop-shadow(0 0 14px var(--accent)); }
.ring-b { stroke: var(--accent-2); stroke-width: 1.2; stroke-dasharray: 10 8; opacity: 0.55; }
.particle { fill: var(--accent-2); opacity: 0.85; animation: neon-drift 6s ease-in-out infinite; }
.underline { fill: var(--accent); filter: drop-shadow(0 0 6px var(--accent)); }
@keyframes neon-drift { 50% { transform: translateY(-18px); } }
:global(html[data-perf="low"]) .particle { animation: none; }
</style>
