<template>
  <div class="page">
    <div class="card">
      <h3 class="title">界面风格</h3>
      <ThemePicker />
    </div>

    <div class="card">
      <h3 class="title">常用入口</h3>
      <div class="row">
        <el-button @click="router.push('/units')">我的房屋</el-button>
        <el-button @click="router.push('/tasks')">待办</el-button>
        <el-button v-if="auth.isCommittee" @click="router.push('/income')">收入表</el-button>
        <el-button @click="router.push('/reports')">财务报表</el-button>
        <el-button @click="logoutNow">退出登录</el-button>
      </div>
    </div>

    <div class="card">
      <h3 class="title">个人资料</h3>
      <div class="row">
        <el-input v-model="profile.nickname" placeholder="昵称" style="max-width: 240px" />
        <el-select v-model="profile.gender" placeholder="性别" clearable style="width: 120px">
          <el-option label="未知" :value="0" /><el-option label="男" :value="1" /><el-option label="女" :value="2" />
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

    <div class="card" v-if="!profile.phone">
      <h3 class="title">绑定手机号</h3>
      <p class="muted">仅微信登录的账号需要先绑定手机号才能做业主认证、注销等操作。若该手机号已注册，两个账号将合并（以该手机号原账号为主）。</p>
      <div class="row">
        <el-input v-model="bind.phone" placeholder="手机号" maxlength="11" style="max-width: 180px" />
        <el-button @click="sendBindCode">发送验证码</el-button>
        <el-input v-model="bind.code" placeholder="验证码" maxlength="6" style="max-width: 140px" />
        <el-button type="primary" @click="bindPhone">绑定</el-button>
      </div>
    </div>

    <div class="card" v-else>
      <h3 class="title">更换手机号</h3>
      <p class="muted">需要原手机号和新手机号各自的验证码。新手机号若已属于其他账号，两个账号将合并（以新手机号原账号为主，身份取高）。</p>
      <div class="row">
        <el-input v-model="change.oldPhone" placeholder="原手机号" maxlength="11" style="max-width: 160px" />
        <el-button @click="sendChangeCode(change.oldPhone)">发送原号验证码</el-button>
        <el-input v-model="change.oldCode" placeholder="原号验证码" maxlength="6" style="max-width: 140px" />
      </div>
      <div class="row" style="margin-top: 8px">
        <el-input v-model="change.newPhone" placeholder="新手机号" maxlength="11" style="max-width: 160px" />
        <el-button @click="sendChangeCode(change.newPhone)">发送新号验证码</el-button>
        <el-input v-model="change.newCode" placeholder="新号验证码" maxlength="6" style="max-width: 140px" />
        <el-button type="primary" @click="changePhone">更换</el-button>
      </div>
    </div>

    <div class="card">
      <h3 class="title">设置密码</h3>
      <el-input v-model="pwd.current" type="password" placeholder="当前密码（首次设置可留空）" show-password />
      <el-input v-model="pwd.password" type="password" placeholder="新密码（8~64 位，含字母和数字）" show-password style="margin-top: 8px" />
      <el-input v-model="pwd.confirm" type="password" placeholder="再次输入新密码" show-password style="margin-top: 8px" />
      <el-button type="primary" style="margin-top: 10px" @click="savePassword">保存密码</el-button>
    </div>

    <div class="card">
      <h3 class="title">邮箱验证</h3>
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

    <div class="card">
      <h3 class="title">账号注销</h3>
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
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { attachmentApi, meApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import ThemePicker from '@/theme/ThemePicker.vue'

const router = useRouter()
const auth = useAuthStore()
const profile = reactive({ nickname: '', gender: 0, phone: '', email: '', avatar_url: '' })
const pwd = reactive({ current: '', password: '', confirm: '' })
const bind = reactive({ phone: '', code: '' })
const change = reactive({ oldPhone: '', newPhone: '', oldCode: '', newCode: '' })
const cancel = reactive({ phone: '', code: '' })
const email = ref('')
const emailCode = ref('')

async function logoutNow() {
  await auth.logout()
  router.replace('/login')
}

async function loadProfile() {
  try {
    Object.assign(profile, await meApi.profile())
    email.value = ''
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(loadProfile)

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

async function sendCode(purpose, target, tip = '验证码已发送') {
  try {
    await meApi.sendCode(purpose, target)
    ElMessage.success(tip)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

const sendBindCode = () => sendCode('BIND_PHONE', bind.phone)
const sendChangeCode = (phone) => sendCode('CHANGE_PHONE', phone)
const sendCancelCode = () => sendCode('CANCEL')

// 合并成功时旧令牌已失效，换用返回的新令牌（IFC-071/072）
async function afterPhoneChange(result) {
  if (result.merged && result.token) {
    auth.setAuth(result.token, null)
    ElMessage.success('账号已合并，已切换到主账号')
  } else {
    const bound = result.auto_bound || []
    if (bound.length) {
      const parts = bound.map((item) => item.specific_part).join('、')
      ElMessage.success(`手机号已绑定，已根据你的手机号自动认证为 ${parts} 的产权业主`)
    } else {
      ElMessage.success('手机号已更新')
    }
  }
  await auth.fetchMe().catch(() => null)
  await loadProfile()
}

async function bindPhone() {
  try {
    await afterPhoneChange(await meApi.bindPhone(bind.phone, bind.code))
    Object.assign(bind, { phone: '', code: '' })
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function changePhone() {
  try {
    await afterPhoneChange(await meApi.changePhone(change.oldPhone, change.newPhone, change.oldCode, change.newCode))
    Object.assign(change, { oldPhone: '', newPhone: '', oldCode: '', newCode: '' })
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

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

async function saveEmail() {
  try {
    Object.assign(profile, await meApi.updateProfile({ email: email.value || null }))
    ElMessage.success('邮箱已保存，请验证')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

const sendEmailCode = () => sendCode('EMAIL_VERIFY')

async function verifyEmail() {
  try {
    await meApi.verifyEmail(emailCode.value)
    ElMessage.success('邮箱已验证')
    loadProfile()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function cancelAccount() {
  try {
    await meApi.cancelAccount(cancel.phone, cancel.code)
    await auth.logout()
    ElMessage.success('账号已注销')
    router.replace('/login')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}
</script>
