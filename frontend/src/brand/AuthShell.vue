<!-- MOD-128 / IFC-327：登录/注册/管理端登录页的品牌外壳（配图栏 + 表单栏）；不渲染任何风格切换入口（REQ-FUNC-078） -->
<template>
  <div class="auth-shell">
    <div class="auth-art" aria-hidden="true"><component :is="art" /></div>
    <div class="auth-panel">
      <div class="auth-card">
        <div class="auth-head">
          <BrandMark :size="46" />
          <div class="auth-head-text">
            <h1 class="auth-brand brand-wordmark">{{ BRAND_NAME }}</h1>
            <p class="auth-sub">{{ subtitle }}</p>
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
import { BRAND_NAME } from './brand'
import BrandMark from './BrandMark.vue'
import { artFor } from './art'

const props = defineProps({
  surface: { type: String, default: 'portal' },
  subtitle: { type: String, default: '' }
})

// 用户端读 ocap_theme 对应的 store，管理端读 ocap_admin_theme 对应的 store（互不影响，AC-227-02）
const themeKey = computed(() => (props.surface === 'admin' ? useAdminThemeStore().current : useThemeStore().current))
const art = computed(() => artFor(themeKey.value))
</script>
