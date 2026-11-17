<!-- MOD-122：邮箱验证页（自 Me.vue 原 84-95、257-276 行迁移） -->
<template>
  <div class="page">
    <div class="card">
      <h3 class="title">邮箱验证</h3>
      <p class="muted">当前邮箱：{{ profile.email || '未填写' }}</p>
      <div class="row">
        <el-input v-model="email" placeholder="邮箱" style="max-width: 260px" />
        <el-button @click="saveEmail">保存邮箱</el-button>
      </div>
      <div class="row" style="margin-top: 8px">
        <el-button @click="sendEmailCode">发送验证码到当前邮箱</el-button>
        <el-input v-model="emailCode" placeholder="验证码" maxlength="6" style="max-width: 140px" />
        <el-button @click="verifyEmail">验证</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { meApi } from '@/shared/api'
import { errorText } from '@/shared/format'
import { useProfile } from './useProfile'

const { profile, loadProfile } = useProfile()
const email = ref('')
const emailCode = ref('')

onMounted(loadProfile)

async function saveEmail() {
  try {
    Object.assign(profile, await meApi.updateProfile({ email: email.value || null }))
    ElMessage.success('邮箱已保存，请验证')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function sendEmailCode() {
  try {
    await meApi.sendCode('EMAIL_VERIFY')
    ElMessage.success('验证码已发送')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function verifyEmail() {
  try {
    await meApi.verifyEmail(emailCode.value)
    ElMessage.success('邮箱已验证')
    loadProfile()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}
</script>
