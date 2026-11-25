<!-- MOD-128：极光 Bento 版配图。极光光斑 + 圆角 Bento 方块拼贴（含芯片电路线）+ 点阵 + 等宽数据条；登录页在主题样式中转为全屏背景 -->
<template>
  <div class="bento-art">
    <span class="glow glow-a" />
    <span class="glow glow-b" />
    <span class="glow glow-c" />
    <svg viewBox="0 0 800 600" preserveAspectRatio="xMidYMid slice" role="presentation" focusable="false">
      <defs>
        <pattern id="art-dots" width="24" height="24" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="1.6" class="dot" />
        </pattern>
      </defs>
      <rect class="dotgrid" x="470" y="40" width="300" height="150" fill="url(#art-dots)" />
      <rect class="tile tile-a" x="90" y="120" width="250" height="170" rx="28" />
      <rect class="tile tile-b" x="360" y="210" width="170" height="170" rx="28" />
      <rect class="tile tile-c" x="550" y="250" width="190" height="120" rx="28" />
      <rect class="tile tile-d" x="130" y="310" width="200" height="130" rx="28" />
      <rect class="tile tile-e" x="360" y="400" width="380" height="90" rx="28" />
      <g class="chip" transform="translate(150 150)">
        <rect x="0" y="0" width="70" height="70" rx="12" />
        <path d="M-14 18h14M-14 35h14M-14 52h14M70 18h14M70 35h14M70 52h14M18 -14v14M35 -14v14M52 -14v14M18 70v14M35 70v14M52 70v14" />
        <rect x="22" y="22" width="26" height="26" rx="6" />
      </g>
      <g class="chip" transform="translate(410 250)">
        <rect x="0" y="0" width="60" height="60" rx="12" />
        <path d="M-12 20h12M-12 40h12M60 20h12M60 40h12M20 -12v12M40 -12v12M20 60v12M40 60v12" />
        <path d="M16 30h28M30 16v28" />
      </g>
      <!-- 装饰字符经 CSS 伪元素输出，不进入文本内容（三套风格的页面文本须一致） -->
      <foreignObject x="390" y="420" width="340" height="50">
        <div class="mono-text" data-t="01 10 11 01 00 10 01 11"></div>
      </foreignObject>
    </svg>
  </div>
</template>

<style scoped>
.bento-art { position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--hero); }
.bento-art svg { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.glow { position: absolute; border-radius: 50%; opacity: 0.5; pointer-events: none; }
.glow-a { width: 55%; padding-top: 55%; left: -12%; top: -18%; background: radial-gradient(circle, var(--accent-2), transparent 68%); }
.glow-b { width: 45%; padding-top: 45%; right: -10%; bottom: -14%; background: radial-gradient(circle, var(--accent), transparent 68%); }
.glow-c { width: 38%; padding-top: 38%; right: 26%; top: -14%; background: radial-gradient(circle, var(--accent), transparent 70%); opacity: 0.35; }
.tile { fill: var(--surface); stroke: var(--line); stroke-width: 1.5; }
.tile-b, .tile-d { fill: var(--glass); }
.tile-e { fill: var(--accent-bg); }
.chip rect { fill: none; stroke: var(--accent-text); stroke-width: 2.5; }
.chip path { fill: none; stroke: var(--accent-text); stroke-width: 2.5; stroke-linecap: round; }
.dot { fill: var(--on-hero); opacity: 0.7; }
.mono-text::before { content: attr(data-t); font-family: var(--mono); font-size: 30px; font-weight: 700; letter-spacing: 3px; color: var(--on-accent); }
</style>
