<template>
  <AuthShell surface="admin" subtitle="管理后台登录">
    <div class="card auth-form-card">
      <form id="admin-password-login" method="post" @submit.prevent="login">
        <el-input id="admin-login-username" v-model="username" name="username" autocomplete="username" placeholder="管理员账号" aria-label="管理员账号" />
        <el-input id="admin-login-password" v-model="password" name="password" type="password" autocomplete="current-password" placeholder="密码" aria-label="密码" show-password style="margin-top: 10px" />
        <el-button type="primary" native-type="submit" style="width: 100%; margin-top: 14px" :loading="loading">登录</el-button>
      </form>
      <p class="muted">管理后台登录不支持"记住我"。</p>
    </div>
  </AuthShell>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { setToken } from '@/shared/http'
import { errorText } from '@/shared/format'
import { useAdminThemeStore } from '@/theme/adminStore'
import AuthShell from '@/brand/AuthShell.vue'
import { saveAdminName } from './adminSession'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function login(event) {
  const fields = event ? new FormData(event.currentTarget) : null
  const account = fields?.get('username') ?? username.value
  const secret = fields?.get('password') ?? password.value
  loading.value = true
  try {
    const result = await admin.login(account, secret)
    setToken(result.token, true)
    saveAdminName(result.admin?.username)
    await useAdminThemeStore().reconcile()
    ElMessage.success('登录成功')
    router.replace('/admin')
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    loading.value = false
  }
}
</script>
