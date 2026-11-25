<!-- MOD-119 / IFC-328：品牌标识（深靛圆角底 + 几何红枫叶 + 青色电路脉络），与 favicon / 小程序图标同源。
     颜色全部落在 brand.css 的类规则里（组件内不写颜色字面量，TC-INT-867）。 -->
<template>
  <svg class="brand-mark" :width="size" :height="size" viewBox="0 0 32 32" aria-hidden="true" focusable="false" style="--brand-accent: var(--accent)">
    <rect class="brand-mark-frame" x="0.6" y="0.6" width="30.8" height="30.8" rx="8.4" />
    <rect class="brand-mark-frame-gloss" x="1.4" y="1.4" width="29.2" height="29.2" rx="7.6" />
    <path
      class="brand-mark-leaf"
      fill="currentColor"
      d="M16 3.6 L18.4 8.6 L20.2 7.4 L19.8 11.4 L24.4 9.8 L22.4 13.8 L27.4 13.4 L24.2 16.6 L28.2 18.4 L23.6 19.4 L24.8 23.4 L20.6 21.6 L20.2 26.2 L17.2 23 L16 28.4 L14.8 23 L11.8 26.2 L11.4 21.6 L7.2 23.4 L8.4 19.4 L3.8 18.4 L7.8 16.6 L4.6 13.4 L9.6 13.8 L7.6 9.8 L12.2 11.4 L11.8 7.4 L13.6 8.6 Z"
    />
    <path class="brand-mark-stem" d="M16 23.2 L16 29.4" />
    <g class="brand-mark-traces">
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
  </svg>
</template>

<script setup>
defineProps({ size: { type: Number, default: 32 } })
</script>
