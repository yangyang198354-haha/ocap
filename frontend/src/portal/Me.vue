<template>
  <div class="page">
    <div class="card">
      <h3 class="title">个人资料</h3>
      <div class="row">
        <el-input v-model="profile.nickname" placeholder="昵称" style="max-width: 240px" />
        <el-select v-model="profile.gender" placeholder="性别" style="width: 120px">
          <el-option label="男" value="MALE" /><el-option label="女" value="FEMALE" /><el-option label="保密" value="UNKNOWN" />
        </el-select>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </div>
      <p class="muted" style="margin-top: 10px">手机号：{{ profile.phone || '未绑定' }}；邮箱：{{ profile.email || '未填写' }}</p>
      <div class="row">
        <el-upload :show-file-list="false" :http-request="uploadAvatar" accept="image/*">
          <el-button>更换头像</el-button>
        </el-upload>
      </div>
    </div>

    <div class="card">
      <h3 class="title">设置密码</h3>
      <el-input v-model="pwd.current" type="password" placeholder="当前密码（首次设置可留空）" show-password />
      <el-input v-model="pwd.password" type="password" placeholder="新密码（8~20 位，含字母和数字）" show-password style="margin-top: 8px" />
      <el-input v-model="pwd.confirm" type="password" placeholder="再次输入新密码" show-password style="margin-top: 8px" />
      <el-button type="primary" style="margin-top: 10px" @click="savePassword">保存密码</el-button>
    </div>

    <div class="card">
      <h3 class="title">邮箱验证</h3>
      <div class="row">
        <el-input v-model="email" placeholder="邮箱" style="max-width: 260px" />
        <el-button @click="sendEmailCode">发送验证码</el-button>
        <el-input v-model="emailCode" placeholder="验证码" maxlength="6" style="max-width: 140px" />
        <el-button @click="verifyEmail">验证</el-button>
      </div>
    </div>

    <div class="card">
      <h3 class="title">账号注销</h3>
      <p class="muted">注销后账号将不可登录，历史记录保留。请先获取验证码。</p>
      <div class="row">
        <el-button @click="sendCancelCode">发送注销验证码</el-button>
        <el-input v-model="cancelCode" placeholder="验证码" maxlength="6" style="max-width: 140px" />
        <el-button type="danger" @click="cancelAccount">确认注销</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { attachmentApi, meApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const router = useRouter()
const auth = useAuthStore()
const profile = reactive({ nickname: '', gender: 'UNKNOWN', phone: '', email: '', avatar_url: '' })
const pwd = reactive({ current: '', password: '', confirm: '' })
const email = ref('')
const emailCode = ref('')
const cancelCode = ref('')

onMounted(async () => {
  try {
    Object.assign(profile, await meApi.profile())
    email.value = profile.email || ''
  } catch (e) {
    ElMessage.error(errorText(e))
  }
})

async function saveProfile() {
  try {
    Object.assign(profile, await meApi.updateProfile({ nickname: profile.nickname, gender: profile.gender }))
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function uploadAvatar({ file }) {
  try {
    const uploaded = await attachmentApi.upload(file, 'AVATAR')
    await meApi.updateProfile({ avatar_attachment_id: uploaded.id })
    ElMessage.success('头像已更新')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function savePassword() {
  const body = { password: pwd.password, confirm: pwd.confirm }
  if (pwd.current) body.current_password = pwd.current
  try {
    await meApi.setPassword(body)
    ElMessage.success('密码已保存')
    Object.assign(pwd, { current: '', password: '', confirm: '' })
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function sendEmailCode() {
  try {
    await meApi.sendCode('EMAIL_VERIFY', email.value)
    ElMessage.success('验证码已发送')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function verifyEmail() {
  try {
    await meApi.verifyEmail(emailCode.value)
    ElMessage.success('邮箱已验证')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function sendCancelCode() {
  try {
    await meApi.sendCode('CANCEL')
    ElMessage.success('验证码已发送')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function cancelAccount() {
  try {
    await meApi.cancelAccount(cancelCode.value)
    await auth.logout()
    ElMessage.success('账号已注销')
    router.replace('/login')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}
</script>
