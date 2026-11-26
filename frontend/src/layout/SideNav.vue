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
        <UiIcon class="side-icon" :name="iconFor(node.key)" />
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
        <UiIcon class="side-icon" :name="iconFor(node.key)" />
        <span class="side-label">{{ node.label }}</span>
      </router-link>
      <Transition name="side-sub" :css="false" @enter="onEnter" @leave="onLeave">
        <ul v-if="node.children && openKey === node.key" :id="`side-sub-${node.key}`" class="side-sub" @keydown.esc="collapse(node.key, $event)">
          <li v-for="(leaf, index) in node.children" :key="leaf.key" :style="{ '--i': index }">
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
      </Transition>
    </template>
  </nav>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { nextOpenKey, resolveActive } from './menus'
import UiIcon from '@/portal/UiIcon.vue'

const ICONS = { home: 'home', units: 'home', resolutions: 'doc', polls: 'vote', claims: 'receipt', income: 'income', reports: 'chart', tasks: 'task', info: 'doc', registry: 'doc', appeals: 'task', memberships: 'home', seats: 'user', flows: 'chart', finance: 'wallet', users: 'user', content: 'doc', audit: 'task' }
const iconFor = (key) => ICONS[key] || 'doc'

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

// 二级菜单展开/收起的高度过渡（MOD-150 / IFC-366）：只动 height，≤280ms；系统"减少动效"或无法测量高度（jsdom）时直接完成。
// matchMedia 在 jsdom 缺失，按"不减少"处理且不抛错
const reducedMotion = () => typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches

function animateHeight(el, from, to, done) {
  el.style.overflow = 'hidden'
  el.style.height = `${from}px`
  void el.offsetHeight // 强制回流，使起始高度生效
  el.style.transition = 'height 280ms ease'
  el.style.height = `${to}px`
  setTimeout(() => {
    el.style.transition = ''
    el.style.height = ''
    el.style.overflow = ''
    done()
  }, 290)
}

function onEnter(el, done) {
  const target = el.scrollHeight
  if (reducedMotion() || !target) return done()
  animateHeight(el, 0, target, done)
}

function onLeave(el, done) {
  const from = el.scrollHeight
  if (reducedMotion() || !from) return done()
  animateHeight(el, from, 0, done)
}

// Esc：收起所属一级并把焦点还给其按钮
function collapse(key, event) {
  const nav = event.currentTarget.closest('.side-nav')
  openKey.value = null
  nextTick(() => nav?.querySelector(`.side-group-toggle[aria-controls="side-sub-${key}"]`)?.focus())
}
</script>
