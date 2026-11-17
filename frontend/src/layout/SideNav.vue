<!-- MOD-120 / IFC-318：左侧一级/二级导航（规则见 ADR-118：同时至多展开一个、直达自动展开、点击一级只展开不导航） -->
<template>
  <nav class="side-nav" :aria-label="ariaLabel">
    <template v-for="node in menu" :key="node.key">
      <button
        v-if="node.children"
        type="button"
        class="side-item side-group-toggle"
        :class="{ 'is-active': active.node && active.node.key === node.key }"
        :aria-expanded="openKey === node.key ? 'true' : 'false'"
        :aria-controls="`side-sub-${node.key}`"
        :aria-current="active.node && active.node.key === node.key ? 'true' : undefined"
        @click="toggle(node.key)"
      >
        <span class="side-label">{{ node.label }}</span>
        <span class="side-caret" aria-hidden="true">{{ openKey === node.key ? '▾' : '▸' }}</span>
      </button>
      <router-link
        v-else
        :to="node.to"
        class="side-item"
        :class="{ 'is-active': active.node && active.node.key === node.key }"
        :aria-current="active.node && active.node.key === node.key ? 'page' : undefined"
      >
        <span class="side-label">{{ node.label }}</span>
      </router-link>
      <ul v-if="node.children && openKey === node.key" :id="`side-sub-${node.key}`" class="side-sub" @keydown.esc="collapse(node.key, $event)">
        <li v-for="leaf in node.children" :key="leaf.key">
          <router-link
            :to="leaf.to"
            class="side-sub-item"
            :class="{ 'is-active': active.leaf && active.leaf.key === leaf.key }"
            :aria-current="active.leaf && active.leaf.key === leaf.key ? 'page' : undefined"
          >
            <span class="side-label">{{ leaf.label }}</span>
            <span v-if="badgeCount(leaf) > 0" class="side-badge">{{ badgeCount(leaf) }}</span>
          </router-link>
        </li>
      </ul>
    </template>
  </nav>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { nextOpenKey, resolveActive } from './menus'

const props = defineProps({
  menu: { type: Array, required: true },
  badges: { type: Object, default: () => ({}) },
  ariaLabel: { type: String, default: '主导航' }
})

const route = useRoute()
const active = computed(() => resolveActive(props.menu, route.path))
const openKey = ref(nextOpenKey(props.menu, route.path))

// 路由变化：当前页属于某个有二级项的一级则展开它，否则全部收起（ADR-118 规则②）
watch(() => route.path, (path) => {
  openKey.value = nextOpenKey(props.menu, path)
})

function toggle(key) {
  openKey.value = openKey.value === key ? null : key
}

const badgeCount = (leaf) => (leaf.badge ? Number(props.badges?.[leaf.badge]) || 0 : 0)

// Esc：收起所属一级并把焦点还给其按钮
function collapse(key, event) {
  const nav = event.currentTarget.closest('.side-nav')
  openKey.value = null
  nextTick(() => nav?.querySelector(`.side-group-toggle[aria-controls="side-sub-${key}"]`)?.focus())
}
</script>
