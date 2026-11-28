<!-- MOD-182 / IFC-401：账号注销面板（自 pages/cancel/index.vue 抽出，供独立页与“个人资料”页 Tab 共用） -->
<template>
  <view>
    <view class="card">
      <view class="title">账号注销</view>
      <view class="muted">注销后账号将不可登录，历史记录保留。需输入已绑定的手机号和验证码；未绑定手机号请先绑定。</view>
      <input v-model="phone" class="field mt-16" maxlength="11" placeholder="已绑定的手机号" />
      <view class="row" style="margin-top: 16rpx">
        <button class="btn btn--compact btn--secondary" @click="sendCode">发送注销验证码</button>
        <input v-model="code" class="field" maxlength="6" placeholder="验证码" style="flex: 1" />
      </view>
      <button class="btn btn--danger" style="margin-top: 24rpx" @click="cancelAccount">确认注销</button>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '@/utils/api'
import { confirmDanger } from '@/utils/confirm'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const phone = ref('')
const code = ref('')

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

async function load() {
  try {
    await auth.fetchMe()
  } catch (e) {
    /* 未登录由 http 统一跳转 */
  }
  phone.value = auth.me?.profile?.phone || ''
}

async function sendCode() {
  if (!/^\d{11}$/.test(phone.value)) return toast('请输入已绑定的手机号')
  try {
    await api.sendMeCode('CANCEL')
    toast('验证码已发送')
  } catch (e) {
    toast(e.message)
  }
}

async function cancelAccount() {
  if (!/^\d{11}$/.test(phone.value)) return toast('请输入已绑定的手机号')
  if (!/^\d{6}$/.test(code.value)) return toast('请输入 6 位验证码')
  if (!(await confirmDanger('cancelAccount'))) return
  try {
    await api.cancelAccount(phone.value, code.value)
    auth.clear()
    uni.reLaunch({ url: '/pages/login/index' })
  } catch (e) {
    toast(e.message)
  }
}

onMounted(load)
</script>
