<!-- MOD-182 / IFC-401：小程序邮箱验证最小页面；复用后端 /me/email/verify（ADR-169） -->
<template>
  <ThemeRoot>
  <view>
    <view class="card">
      <view class="title">邮箱验证</view>
      <view class="muted">当前邮箱：{{ auth.me?.profile?.email || '未填写' }}</view>
      <input v-model="email" class="field mt-16" type="text" placeholder="邮箱" />
      <button style="margin-top: 16rpx" @click="saveEmail">保存邮箱</button>
      <view class="row" style="margin-top: 16rpx">
        <button size="mini" @click="sendCode">发送验证码</button>
        <input v-model="code" class="field" maxlength="6" placeholder="验证码" style="flex: 1" />
      </view>
      <button class="btn" style="margin-top: 24rpx" @click="verify">验证</button>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const email = ref('')
const code = ref('')
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

async function load() {
  try {
    await auth.fetchMe()
  } catch (e) {
    /* 未登录由 http 统一跳转 */
  }
  email.value = auth.me?.profile?.email || ''
}

async function saveEmail() {
  const value = email.value.trim()
  if (!EMAIL_RE.test(value)) return toast('请输入正确的邮箱')
  try {
    await api.updateProfile({ email: value })
    toast('邮箱已保存，请验证')
    await auth.fetchMe().catch(() => null)
  } catch (e) {
    toast(e.message)
  }
}

async function sendCode() {
  if (!EMAIL_RE.test(email.value.trim())) return toast('请先保存正确的邮箱')
  try {
    await api.sendMeCode('EMAIL_VERIFY')
    toast('验证码已发送')
  } catch (e) {
    toast(e.message)
  }
}

async function verify() {
  if (!/^\d{6}$/.test(code.value)) return toast('请输入 6 位验证码')
  try {
    await api.verifyEmail(email.value.trim(), code.value)
    toast('邮箱已验证')
    await auth.fetchMe().catch(() => null)
    uni.navigateBack()
  } catch (e) {
    toast(e.message)
  }
}

onShow(load)
</script>
