<!-- MOD-128：霓虹玻璃版配图。透视网格地平线 + 发光玻璃六边形 + 漂移粒子；颜色全部取语义变量 -->
<template>
  <svg class="neon-art" viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice" role="presentation" focusable="false">
    <rect class="bg" width="800" height="600" />
    <g class="grid">
      <line v-for="l in vLines" :key="`v${l.x}`" :x1="l.x1" y1="600" :x2="400" y2="300" />
      <line v-for="y in hLines" :key="`h${y}`" x1="0" :y1="y" x2="800" :y2="y" />
    </g>
    <g class="glass">
      <polygon class="hex hex-a" points="250,120 310,85 370,120 370,190 310,225 250,190" />
      <polygon class="hex hex-b" points="340,170 420,125 500,170 500,260 420,305 340,260" />
      <polygon class="hex hex-c" points="470,90 520,62 570,90 570,148 520,176 470,148" />
    </g>
    <g class="dots">
      <circle v-for="p in particles" :key="p.id" class="particle" :cx="p.x" :cy="p.y" :r="p.r" :style="{ animationDelay: p.d + 's' }" />
    </g>
    <rect class="underline" x="60" y="520" width="180" height="3" rx="1.5" />
  </svg>
</template>

<script setup>
// 灭点 (400,300)：竖线由底边等距点收束，横线按平方间距加密，形成透视网格
const vLines = Array.from({ length: 17 }, (_, i) => ({ x: -400 + i * 100, x1: -400 + i * 100 }))
const hLines = Array.from({ length: 8 }, (_, i) => Math.round(300 + 300 * ((i + 1) / 8) ** 2))
const particles = Array.from({ length: 8 }, (_, i) => ({
  id: i, x: 120 + i * 80, y: 140 + ((i * 53) % 220), r: 2 + (i % 3), d: -i * 0.9
}))
</script>

<style scoped>
.neon-art { display: block; width: 100%; height: 100%; }
.bg { fill: var(--bg); }
.grid line { stroke: var(--accent); stroke-width: 1; opacity: 0.35; }
.hex { fill: var(--accent); fill-opacity: 0.12; stroke: var(--accent-2); stroke-width: 2; filter: drop-shadow(0 0 8px var(--accent)); }
.hex-b { stroke: var(--accent); filter: drop-shadow(0 0 10px var(--accent-2)); }
.hex-c { fill-opacity: 0.2; }
.particle { fill: var(--accent-2); opacity: 0.85; animation: neon-drift 6s ease-in-out infinite; }
.underline { fill: var(--accent); filter: drop-shadow(0 0 6px var(--accent)); }
@keyframes neon-drift { 50% { transform: translateY(-18px); } }
:global(html[data-perf="low"]) .particle { animation: none; }
</style>
