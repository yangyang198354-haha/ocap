<template>
  <div class="theme-picker" role="radiogroup" aria-label="界面风格">
    <button
      v-for="item in store.list"
      :key="item.key"
      type="button"
      role="radio"
      class="theme-option"
      :class="{ 'is-selected': store.current === item.key }"
      :aria-checked="store.current === item.key"
      :data-theme-key="item.key"
      @click="pick(item.key)"
    >
      <span class="theme-swatch" aria-hidden="true">
        <i v-for="(c, i) in item.swatch" :key="i" :style="{ background: c }" />
      </span>
      <span class="theme-name">{{ item.name }}</span>
      <span v-if="store.current === item.key" class="theme-check">已选</span>
    </button>
  </div>
</template>

<script setup>
import { ElMessage } from 'element-plus'
import { useThemeStore } from './store'

const store = useThemeStore()

async function pick(key) {
  if (key === store.current) return
  try {
    await store.select(key)
  } catch (e) {
    ElMessage.error('保存失败，已恢复原风格，请稍后重试')
  }
}
</script>

<style scoped>
.theme-picker { display: flex; gap: 12px; flex-wrap: wrap; }
.theme-option {
  display: flex; flex-direction: column; align-items: center; gap: 8px; min-width: 120px; min-height: var(--hit-min);
  padding: 12px; cursor: pointer; font: inherit; color: var(--text);
  background: var(--surface); border: 2px solid var(--line); border-radius: var(--radius-md);
}
.theme-option.is-selected { border-color: var(--accent); }
.theme-swatch { display: flex; width: 72px; height: 28px; border-radius: 8px; overflow: hidden; border: 1px solid var(--line); }
.theme-swatch i { flex: 1; }
.theme-name { font-size: 14px; }
.theme-check { font-size: 12px; color: var(--accent-text); }
</style>
