<template>
  <view class="card">
    <view class="title">业主委员会 · 登录</view>
    <input v-model="phone" placeholder="手机号" maxlength="11" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-bottom: 16rpx" />
    <view class="row">
      <input v-model="code" placeholder="验证码" maxlength="6" style="flex: 1; border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx" />
      <button size="mini" :disabled="left > 0" @click="send">{{ left ? `${left}s` : '获取验证码' }}</button>
    </view>
    <button class="btn" style="margin-top: 24rpx" @click="loginCode">验证码登录</button>
    <button style="margin-top: 16rpx" @click="loginWechat">微信一键登录</button>
    <view class="muted" style="margin-top: 16rpx">未注册手机号验证后将自动创建账号。</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const phone = ref('')
const code = ref('')
const left = ref(0)

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

async function send() {
  try {
    await api.sendCode(phone.value, 'LOGIN')
    left.value = 60
    const timer = setInterval(() => {
      left.value -= 1
      if (left.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    toast(e.message)
  }
}

async function afterLogin(result) {
  auth.setAuth(result.token, result.user)
  const me = await auth.fetchMe()
  uni.reLaunch({ url: me && me.profile_completed === false ? '/pages/profile-setup/index' : '/pages/index/index' })
}

async function loginCode() {
  try {
    await afterLogin(await api.loginByCode(phone.value, code.value))
  } catch (e) {
    toast(e.message)
  }
}

function loginWechat() {
  uni.login({
    provider: 'weixin',
    success: async ({ code: wxCode }) => {
      try {
        await afterLogin(await api.loginByWechat(wxCode))
      } catch (e) {
        toast(e.message)
      }
    }
  })
}
</script>
