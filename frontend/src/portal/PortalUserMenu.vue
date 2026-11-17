<!-- MOD-121 / IFC-321：右上角昵称与下拉用户菜单（悬停或点击展开；7 个个人中心项 + 退出登录） -->
<template>
  <el-dropdown :trigger="['hover', 'click']" @command="onCommand">
    <button type="button" class="user-menu-trigger" :title="fullName">
      <span class="user-menu-name">{{ displayName }}</span>
      <svg width="10" height="6" viewBox="0 0 10 6" aria-hidden="true">
        <path d="M1 1l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.5" />
      </svg>
    </button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item v-for="item in PORTAL_USER_MENU" :key="item.key" :command="item.to">{{ item.label }}</el-dropdown-item>
        <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'
import { PORTAL_USER_MENU } from '@/layout/menus'
import { truncateLabel } from '@/layout/labels'

const router = useRouter()
const auth = useAuthStore()

// 昵称为空显示"业主"；超过 12 个字截断，完整名放 title（AC-212-04）
const fullName = computed(() => auth.me?.profile?.nickname || '业主')
const displayName = computed(() => truncateLabel(fullName.value, 12))

async function onCommand(command) {
  if (command === 'logout') {
    await auth.logout()
    useHousingStore().$reset()
    router.replace('/login')
    return
  }
  router.push(command)
}
</script>
