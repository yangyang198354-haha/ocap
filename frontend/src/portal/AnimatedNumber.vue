<template>
  <span ref="el" class="animated-number">{{ display }}</span>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

// 数字动效：首次入场从 0 缓动到目标值；之后数值变化走交叉淡化，不重播入场
const props = defineProps({
  value: { type: [Number, String], default: 0 },
  decimals: { type: Number, default: 0 },
  prefix: { type: String, default: '' },
  suffix: { type: String, default: '' },
  duration: { type: Number, default: 700 }
})

const el = ref(null)
const display = ref('')
let raf = null
let fadeTimer = null
let mounted = false

const reduced = () => {
  if (typeof window === 'undefined') return true
  // 测试环境直接渲染终值，避免断言依赖动画帧时序
  if (import.meta.env?.MODE === 'test') return true
  if (document.documentElement.dataset.perf === 'low') return true
  return Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches)
}

const format = (n) => {
  const num = Number(n)
  const safe = Number.isFinite(num) ? num : 0
  return `${props.prefix}${safe.toLocaleString('en-US', {
    minimumFractionDigits: props.decimals,
    maximumFractionDigits: props.decimals
  })}${props.suffix}`
}

const target = () => {
  const num = Number(props.value)
  return Number.isFinite(num) ? num : 0
}

// 首帧即渲染终值：降级/测试环境不会闪；可动效时由 onMounted 从 0 开始滚动
display.value = reduced() ? format(target()) : ''

const stopRaf = () => {
  if (raf) cancelAnimationFrame(raf)
  raf = null
}

const playCountUp = () => {
  const to = target()
  if (reduced() || typeof requestAnimationFrame !== 'function') {
    display.value = format(to)
    return
  }
  stopRaf()
  display.value = format(0)
  const start = performance.now()
  const step = (now) => {
    const t = Math.min(1, (now - start) / props.duration)
    const eased = 1 - Math.pow(1 - t, 3)
    display.value = format(to * eased)
    if (t < 1) raf = requestAnimationFrame(step)
  }
  raf = requestAnimationFrame(step)
}

// 更新：旧值淡出 120ms，换值后用 180ms 淡入（不做二次滚动）
const crossfade = (next) => {
  if (!el.value) {
    display.value = format(next)
    return
  }
  if (reduced()) {
    display.value = format(next)
    return
  }
  el.value.style.transition = 'opacity 120ms ease'
  el.value.style.opacity = '0'
  clearTimeout(fadeTimer)
  fadeTimer = setTimeout(() => {
    display.value = format(next)
    el.value.style.transition = 'opacity 180ms ease'
    el.value.style.opacity = '1'
  }, 120)
}

onMounted(() => {
  mounted = true
  playCountUp()
})

watch(() => [props.value, props.decimals, props.prefix, props.suffix], () => {
  if (!mounted) return
  stopRaf()
  crossfade(target())
})

onBeforeUnmount(() => {
  stopRaf()
  clearTimeout(fadeTimer)
})
</script>

<style scoped>
.animated-number {
  font-variant-numeric: tabular-nums;
  display: inline-block;
}
</style>
