<!-- MOD-120 / IFC-319：窄屏页顶二级项切换条（宽屏由 CSS 隐藏） -->
<template>
  <nav class="sub-nav-bar" aria-label="分区切换">
    <router-link
      v-for="item in items"
      :key="item.key"
      :to="item.to"
      class="sub-nav-item"
      :class="{ 'is-active': current && current.key === item.key }"
      :aria-current="current && current.key === item.key ? 'page' : undefined"
    >
      <span>{{ item.label }}</span>
      <span v-if="badgeCount(item) > 0" class="side-badge">{{ badgeCount(item) }}</span>
    </router-link>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { isPathMatch } from './menus'

const props = defineProps({
  items: { type: Array, required: true },
  badges: { type: Object, default: () => ({}) }
})

const route = useRoute()
const current = computed(() =>
  props.items.find((item) => item.to === route.path) ||
  props.items.find((item) => (item.activeOn || []).some((pattern) => isPathMatch(route.path, pattern))) ||
  null)
const badgeCount = (item) => (item.badge ? Number(props.badges?.[item.badge]) || 0 : 0)
</script>
