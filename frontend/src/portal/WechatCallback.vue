<template>
  <div class="page" style="max-width: 420px; padding-top: 80px">
    <div class="card">
      <p>正在完成微信登录…</p>
      <p v-if="error" style="color: #d93025">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const error = ref('')

onMounted(async () => {
  const code = route.query.code
  if (!code) {
    error.value = '缺少微信授权码'
    return
  }
  try {
    const result = await authApi.wechatExchange(String(code))
    auth.setAuth(result.token, result.user)
    router.replace('/')
  } catch (e) {
    error.value = e.message || '微信登录失败'
  }
})
</script>
