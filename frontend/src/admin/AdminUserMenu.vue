<!-- MOD-125 / IFC-326：管理端右上角管理员菜单（风格切换并入、退出登录；不含个人资料类项，C-69）
     触发器保留 admin-theme-trigger 类名：沿用既有"管理端风格入口"选择器（风格切换已并入本菜单） -->
<template>
  <el-dropdown :trigger="['hover', 'click']" @command="onCommand">
    <button type="button" class="user-menu-trigger admin-theme-trigger" :title="fullName">
      <span class="user-menu-name">{{ displayName }}</span>
      <svg width="10" height="6" viewBox="0 0 10 6" aria-hidden="true">
        <path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5" />
      </svg>
    </button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item v-for="theme in store.list" :key="theme.key" :command="`theme:${theme.key}`">
          <svg class="theme-swatch" viewBox="0 0 34 14" aria-hidden="true">
            <circle cx="7" cy="7" r="5" :fill="theme.swatch[0]" />
            <circle cx="17" cy="7" r="5" :fill="theme.swatch[1]" />
            <circle cx="27" cy="7" r="5" :fill="theme.swatch[2]" />
          </svg>
          <span>{{ theme.name }}</span>
          <span v-if="theme.key === store.current" class="muted muted-gap">已选</span>
        </el-dropdown-item>
        <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { setToken } from '@/shared/http'
import { useAdminThemeStore } from '@/theme/adminStore'
import { truncateLabel } from '@/layout/labels'
import { clearAdminName, readAdminName } from './adminSession'

const router = useRouter()
const store = useAdminThemeStore()

// 取不到账号名显示"管理员"；超过 12 个字截断，完整名放 title（AC-226-05）
const fullName = computed(() => readAdminName() || '管理员')
const displayName = computed(() => truncateLabel(fullName.value, 12))

async function pickTheme(key) {
  if (key === store.current) return
  try {
    await store.select(key)
  } catch (e) {
    ElMessage.error('保存失败，已恢复原风格，请稍后重试')
  }
}

function logout() {
  setToken('', true)
  clearAdminName()
  store.resetSession()
  router.replace('/admin/login')
}

function onCommand(command) {
  if (command === 'logout') return logout()
  if (typeof command === 'string' && command.startsWith('theme:')) return pickTheme(command.slice(6))
}
</script>
