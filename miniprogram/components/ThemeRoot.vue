<template>
  <view class="theme-root" :class="`theme-${theme.current}`" :style="theme.cssVarsText">
    <slot />
  </view>
</template>

<script setup>
// MOD-028 / IFC-149：注入当前风格的 CSS 变量，并同步原生 tabBar / 导航栏。
import { onMounted, watch } from 'vue'
import { useThemeStore } from '@/store/theme'

const theme = useThemeStore()

onMounted(() => theme.applyNative(theme.current))
watch(() => theme.current, (key) => theme.applyNative(key))
</script>

<style>
.theme-root { min-height: 100vh; background: var(--bg); color: var(--text); font-family: var(--font); }
</style>
