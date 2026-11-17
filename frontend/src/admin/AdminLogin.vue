<template>
  <AuthShell surface="admin" subtitle="管理后台登录">
    <div class="card auth-form-card">
      <el-input v-model="username" placeholder="管理员账号" />
      <el-input v-model="password" type="password" placeholder="密码" show-password style="margin-top: 10px" />
      <el-button type="primary" style="width: 100%; margin-top: 14px" :loading="loading" @click="login">登录</el-button>
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

async function login() {
  loading.value = true
  try {
    const result = await admin.login(username.value, password.value)
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
