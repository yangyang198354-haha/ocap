<!-- MOD-175 / IFC-396：右上角用户菜单分“个人设置/系统设置”两组；400ms 过渡 + 180ms 悬停意图（ADR-168）
     既有能力保留：昵称左侧头像、昵称截断、退出登录置底 -->
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
        <template v-for="(group, index) in USER_MENU_GROUPS" :key="group.key">
          <li v-if="index > 0" class="user-menu-separator" role="separator"></li>
          <li class="user-menu-group-title" role="presentation">{{ group.label }}</li>
          <el-dropdown-item v-for="item in group.items" :key="item.key" :command="item.to">{{ item.label }}</el-dropdown-item>
        </template>
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
import { USER_MENU_GROUPS, USER_MENU_TIMING } from '@/layout/menus'
import { truncateLabel } from '@/layout/labels'
import AuthImage from './parts/AuthImage.vue'

const router = useRouter()
const auth = useAuthStore()
const allowedCommands = new Set(USER_MENU_GROUPS.flatMap((group) => group.items.map((item) => item.to)))

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
