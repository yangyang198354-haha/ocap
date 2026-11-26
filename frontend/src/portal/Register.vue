<template>
  <AuthShell surface="portal" subtitle="手机号注册">
    <div class="card auth-form-card">
      <el-input v-model="form.phone" placeholder="手机号" maxlength="11" />
      <div class="row" style="margin-top: 10px">
        <el-input v-model="form.code" placeholder="验证码" maxlength="6" style="flex: 1" />
        <el-button :disabled="left > 0" @click="send">{{ left ? `${left}s` : '获取验证码' }}</el-button>
      </div>
      <el-button type="primary" style="width: 100%; margin-top: 14px" :loading="loading" @click="submit">注册并登录</el-button>
      <div class="row" style="justify-content: space-between; margin-top: 12px">
        <router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </AuthShell>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import { useThemeStore } from '@/theme/store'
import AuthShell from '@/brand/AuthShell.vue'

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
    // 手机号匹配到清册专有部分：进入"认证产权"页由用户确认后绑定（REQ-FUNC-234/236）；否则进入主页
    router.replace(result.registry_match?.pending ? '/units/pick' : '/')
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    loading.value = false
  }
}
</script>
