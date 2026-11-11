<template>
  <el-dropdown trigger="click" @command="pick">
    <button type="button" class="admin-theme-trigger">
      <span>{{ currentTheme ? currentTheme.name : '风格' }}</span>
      <svg width="10" height="6" viewBox="0 0 10 6" aria-hidden="true">
        <path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5" />
      </svg>
    </button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item v-for="theme in store.list" :key="theme.key" :command="theme.key">
          <svg class="theme-swatch" viewBox="0 0 34 14" aria-hidden="true">
            <circle cx="7" cy="7" r="5" :fill="theme.swatch[0]" />
            <circle cx="17" cy="7" r="5" :fill="theme.swatch[1]" />
            <circle cx="27" cy="7" r="5" :fill="theme.swatch[2]" />
          </svg>
          <span>{{ theme.name }}</span>
          <span v-if="theme.key === store.current" class="muted muted-gap">已选</span>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAdminThemeStore } from './adminStore'

const store = useAdminThemeStore()
const currentTheme = computed(() => store.list.find((theme) => theme.key === store.current))

async function pick(key) {
  if (key === store.current) return
  try {
    await store.select(key)
  } catch (e) {
    ElMessage.error('保存失败，已恢复原风格，请稍后重试')
  }
}
</script>
