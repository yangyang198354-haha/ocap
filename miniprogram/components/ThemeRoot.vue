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
/* padding-top 阻断首个子元素的 margin 折叠：折叠后卡片外边距会跑到 .theme-root 背景之外，露出 page 默认底色（浅色横条） */
.theme-root { min-height: 100vh; padding-top: 1rpx; box-sizing: border-box; background: var(--bg); color: var(--text); font-family: var(--font); }
</style>
