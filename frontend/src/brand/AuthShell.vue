<!-- MOD-128 / IFC-327：登录/注册/管理端登录页的品牌外壳（配图栏 + 表单栏）；不渲染任何风格切换入口（REQ-FUNC-078） -->
<template>
  <div class="auth-shell">
    <div class="auth-art" aria-hidden="true">
      <component :is="art" />
      <TerminalMatrix v-if="themeKey === 'terminal'" />
      <div class="auth-art-copy">
        <template v-if="themeKey === 'terminal'">
          <TerminalCommands />
        </template>
        <template v-else-if="themeKey === 'neon'">
          <BrandMark :size="160" />
          <h2><BrandWordmark /></h2>
          <p class="auth-art-english">Cyber@HFL</p>
          <p class="auth-art-tagline">AI 驱动的智能社区平台</p>
        </template>
        <template v-else>
          <h2>欢迎回来</h2>
          <p class="auth-art-tagline">进入您的智能社区空间</p>
        </template>
      </div>
    </div>
    <div class="auth-panel">
      <div class="auth-card">
        <div class="auth-head" :class="{ 'auth-head--title-only': themeKey === 'neon' && !subtitle }">
          <BrandMark v-if="themeKey !== 'neon'" :size="46" />
          <div class="auth-head-text">
            <h1 class="auth-brand brand-wordmark"><BrandWordmark /></h1>
            <p v-if="subtitle" class="auth-sub">{{ subtitle }}</p>
          </div>
        </div>
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useThemeStore } from '@/theme/store'
import { useAdminThemeStore } from '@/theme/adminStore'
import BrandMark from './BrandMark.vue'
import BrandWordmark from './BrandWordmark.vue'
import TerminalCommands from './TerminalCommands.vue'
import TerminalMatrix from './TerminalMatrix.vue'
import { artFor } from './art'

const props = defineProps({
  surface: { type: String, default: 'portal' },
  subtitle: { type: String, default: '' }
})

// 用户端读 ocap_theme 对应的 store，管理端读 ocap_admin_theme 对应的 store（互不影响，AC-227-02）
const themeKey = computed(() => (props.surface === 'admin' ? useAdminThemeStore().current : useThemeStore().current))
const art = computed(() => artFor(themeKey.value))
</script>
