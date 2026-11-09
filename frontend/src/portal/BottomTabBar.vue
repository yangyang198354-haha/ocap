<template>
  <nav class="tabbar" aria-label="主导航">
    <router-link v-for="tab in tabs" :key="tab.to" :to="tab.to" :class="{ 'is-active': isActive(tab.to) }">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path :d="tab.icon" />
      </svg>
      <span>{{ tab.label }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

// IFC-148：固定 5 项；每项图标 + 文字标签
const tabs = [
  { label: '首页', to: '/', icon: 'M3 11l9-8 9 8M5 10v10h14V10' },
  { label: '决议', to: '/resolutions', icon: 'M6 3h9l4 4v14H6zM14 3v5h5M9 13h6M9 17h6' },
  { label: '投票', to: '/polls', icon: 'M4 20V10M10 20V4M16 20v-8M22 20H2' },
  { label: '报销', to: '/claims', icon: 'M4 7h16v12H4zM4 7l2-3h12l2 3M12 11v4M10 13h4' },
  { label: '我的', to: '/me', icon: 'M12 12a4 4 0 100-8 4 4 0 000 8zM4 21a8 8 0 0116 0' }
]

// 当前项：路径前缀匹配，'/' 仅精确匹配
const isActive = (to) => (to === '/' ? route.path === '/' : route.path === to || route.path.startsWith(`${to}/`))
</script>
