<template>
  <div class="page" style="max-width: 420px; padding-top: 80px">
    <div class="card">
      <p>正在完成微信登录…</p>
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { useThemeStore } from '@/theme/store'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const error = ref('')

onMounted(async () => {
  // 后端回调重定向到 /login/wechat?ticket=<一次性票据>，失败为 ?error=<code>（IFC-029）
  const ticket = route.query.ticket
  if (!ticket) {
    error.value = route.query.error ? `微信登录失败（${route.query.error}）` : '缺少登录票据'
    return
  }
  try {
    const result = await authApi.wechatExchange(String(ticket))
    auth.setAuth(result.token, result.user)
    await useThemeStore().reconcileAfterLogin()
    router.replace('/')
  } catch (e) {
    error.value = e.message || '微信登录失败'
  }
})
</script>
