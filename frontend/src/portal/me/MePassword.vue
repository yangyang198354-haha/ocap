<!-- MOD-122：设置密码页（自 Me.vue 原 76-82、245-255 行迁移） -->
<template>
  <div class="page">
    <div class="card">
      <h3 class="title">设置密码</h3>
      <el-input v-model="pwd.current" type="password" placeholder="当前密码（首次设置可留空）" show-password />
      <el-input v-model="pwd.password" type="password" placeholder="新密码（8~64 位，含字母和数字）" show-password style="margin-top: 8px" />
      <el-input v-model="pwd.confirm" type="password" placeholder="再次输入新密码" show-password style="margin-top: 8px" />
      <el-button type="primary" style="margin-top: 10px" @click="savePassword">保存密码</el-button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { meApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const pwd = reactive({ current: '', password: '', confirm: '' })

async function savePassword() {
  const body = { password: pwd.password, password_confirm: pwd.confirm }
  if (pwd.current) body.current_password = pwd.current
  try {
    await meApi.setPassword(body)
    ElMessage.success('密码已保存')
    Object.assign(pwd, { current: '', password: '', confirm: '' })
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}
</script>
