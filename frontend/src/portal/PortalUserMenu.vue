<!-- MOD-175 / IFC-396：右上角用户菜单仅“个人资料/系统设置”两个入口；400ms 过渡 + 180ms 悬停意图（ADR-168）
     绑定手机/设置密码/邮箱验证/账号注销在个人资料页内以 Tab 呈现；既有能力保留：昵称左侧头像、昵称截断、退出登录置底 -->
<template>
  <el-dropdown
    :trigger="['hover', 'click']"
    :show-timeout="USER_MENU_TIMING.hoverIntentMs"
    :hide-timeout="USER_MENU_TIMING.hoverIntentMs"
    popper-class="user-menu-popper"
    @command="onCommand"
  >
    <button type="button" class="user-menu-trigger" :title="fullName">
      <AuthImage :src="auth.me?.profile?.avatar_url" alt="默认头像" :size="28" class="user-menu-avatar" />
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
import { PORTAL_USER_MENU, USER_MENU_TIMING } from '@/layout/menus'
import { truncateLabel } from '@/layout/labels'
import AuthImage from './parts/AuthImage.vue'

const router = useRouter()
const auth = useAuthStore()
const allowedCommands = new Set(PORTAL_USER_MENU.map((item) => item.to))

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
  // 只接受配置内的目标地址，未知命令忽略
  if (!allowedCommands.has(command)) return
  router.push(command)
}
</script>

<style scoped>
.user-menu-trigger { display: inline-flex; align-items: center; gap: 8px; }
.user-menu-avatar { flex: none; }
</style>
