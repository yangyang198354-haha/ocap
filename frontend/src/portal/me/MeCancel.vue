<!-- MOD-122：账号注销页（自 Me.vue 原 97-106、278-288 行迁移；二次确认 confirmDanger('cancelAccount') 不变） -->
<template>
  <div class="page">
    <PageHead title="账号注销" />
    <div class="card">
      <p class="muted">注销后账号将不可登录，历史记录保留。需输入已绑定的手机号和验证码；未绑定手机号请先绑定。</p>
      <div class="row">
        <el-input v-model="cancel.phone" placeholder="已绑定的手机号" maxlength="11" style="max-width: 160px" />
        <el-button @click="sendCancelCode">发送注销验证码</el-button>
        <el-input v-model="cancel.code" placeholder="验证码" maxlength="6" style="max-width: 140px" />
        <el-button type="danger" @click="cancelAccount">确认注销</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { meApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'
import { errorText } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'

const router = useRouter()
const auth = useAuthStore()
const cancel = reactive({ phone: '', code: '' })

async function sendCancelCode() {
  try {
    await meApi.sendCode('CANCEL')
    ElMessage.success('验证码已发送')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function cancelAccount() {
  if (!(await confirmDanger('cancelAccount'))) return
  try {
    await meApi.cancelAccount(cancel.phone, cancel.code)
    await auth.logout()
    useHousingStore().$reset()
    ElMessage.success('账号已注销')
    router.replace('/login')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}
</script>
