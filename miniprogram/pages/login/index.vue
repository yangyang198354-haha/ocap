<template>
  <ThemeRoot>
  <view class="card">
    <view class="title">业主委员会 · 登录</view>
    <view class="row" style="margin-bottom: 16rpx">
      <button size="mini" :type="mode === 'code' ? 'primary' : 'default'" @click="mode = 'code'">验证码登录</button>
      <button size="mini" :type="mode === 'password' ? 'primary' : 'default'" @click="mode = 'password'">密码登录</button>
    </view>
    <template v-if="mode === 'code'">
      <input v-model="phone" placeholder="手机号" maxlength="11" class="field" style="margin-bottom: 16rpx" />
      <view class="row">
        <input v-model="code" placeholder="验证码" maxlength="6" class="field" style="flex: 1" />
        <button size="mini" :disabled="left > 0" @click="send">{{ left ? `${left}s` : '获取验证码' }}</button>
      </view>
      <button class="btn" style="margin-top: 24rpx" @click="loginCode">登录</button>
    </template>
    <template v-else>
      <input v-model="identifier" placeholder="账号 / 手机号" class="field" style="margin-bottom: 16rpx" />
      <input v-model="password" password placeholder="密码" class="field" />
      <button class="btn" style="margin-top: 24rpx" @click="loginPassword">登录</button>
    </template>
    <button style="margin-top: 16rpx" @click="loginWechat">微信一键登录</button>
    <view class="muted" style="margin-top: 16rpx">未注册的手机号不会自动创建账号，请先在 Web 端注册，或使用微信一键登录。</view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { ref } from 'vue'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'
import { useThemeStore } from '@/store/theme'

const auth = useAuthStore()
const mode = ref('code')
const phone = ref('')
const code = ref('')
const identifier = ref('')
const password = ref('')
const left = ref(0)
const themeStore = useThemeStore()

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

// 登录响应的 is_new 为 true（仅新建账号的那一次登录）才进入头像昵称设置页（REQ-FUNC-065 / IFC-027）
async function afterLogin(result) {
  auth.setAuth(result.token, null)
  await auth.fetchMe()
  // 先对账账号级风格再跳转（ADR-027 第 4 条）
  await themeStore.reconcileAfterLogin()
  uni.reLaunch({ url: result.is_new === true ? '/pages/profile-setup/index' : '/pages/index/index' })
}

async function loginCode() {
  try {
    await afterLogin(await api.loginByCode(phone.value, code.value))
  } catch (e) {
    toast(e.message)
  }
}

async function loginPassword() {
  try {
    await afterLogin(await api.loginByPassword(identifier.value, password.value))
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
