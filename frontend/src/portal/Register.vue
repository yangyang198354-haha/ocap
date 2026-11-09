<template>
  <div class="page" style="max-width: 420px; padding-top: 60px">
    <div class="card">
      <h2 class="title">手机号注册</h2>
      <el-input v-model="form.phone" placeholder="手机号" maxlength="11" />
      <div class="row" style="margin-top: 10px">
        <el-input v-model="form.code" placeholder="验证码" maxlength="6" style="flex: 1" />
        <el-button :disabled="left > 0" @click="send">{{ left ? `${left}s` : '获取验证码' }}</el-button>
      </div>
      <el-button type="primary" style="width: 100%; margin-top: 14px" :loading="loading" @click="submit">注册并登录</el-button>
      <div class="row" style="justify-content: space-between; margin-top: 12px">
        <router-link to="/login">返回登录</router-link>
        <span class="muted">注册后可通过业主清册认证为产权业主</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import { useThemeStore } from '@/theme/store'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const left = ref(0)
const form = reactive({ phone: '', code: '' })

async function send() {
  try {
    await authApi.sendCode(form.phone, 'REGISTER')
    left.value = 60
    const timer = setInterval(() => {
      left.value -= 1
      if (left.value <= 0) clearInterval(timer)
    }, 1000)
    ElMessage.success('验证码已发送')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submit() {
  loading.value = true
  try {
    const result = await authApi.register(form.phone, form.code)
    auth.setAuth(result.token, result.user)
    await useThemeStore().reconcileAfterLogin()
    ElMessage.success('注册成功')
    router.replace('/')
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    loading.value = false
  }
}
</script>
