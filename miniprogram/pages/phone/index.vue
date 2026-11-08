<template>
  <view>
    <view class="card" v-if="!hasPhone">
      <view class="title">绑定手机号</view>
      <view class="muted">若该手机号已注册，两个账号将合并（以该手机号原账号为主）。</view>
      <input v-model="phone" placeholder="手机号" maxlength="11" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx" />
      <view class="row" style="margin-top: 16rpx">
        <input v-model="code" placeholder="验证码" maxlength="6" style="flex: 1; border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx" />
        <button size="mini" @click="sendCode('BIND_PHONE', phone)">获取验证码</button>
      </view>
      <button class="btn" style="margin-top: 24rpx" @click="bind">绑定</button>
    </view>
    <view class="card" v-else>
      <view class="title">更换手机号</view>
      <view class="muted">需要原手机号与新手机号各自的验证码。新手机号若已属于其他账号，两个账号将合并（以新手机号原账号为主）。</view>
      <input v-model="oldPhone" placeholder="原手机号" maxlength="11" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx" />
      <view class="row" style="margin-top: 16rpx">
        <input v-model="oldCode" placeholder="原号验证码" maxlength="6" style="flex: 1; border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx" />
        <button size="mini" @click="sendCode('CHANGE_PHONE', oldPhone)">获取</button>
      </view>
      <input v-model="newPhone" placeholder="新手机号" maxlength="11" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; margin-top: 16rpx" />
      <view class="row" style="margin-top: 16rpx">
        <input v-model="newCode" placeholder="新号验证码" maxlength="6" style="flex: 1; border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx" />
        <button size="mini" @click="sendCode('CHANGE_PHONE', newPhone)">获取</button>
      </view>
      <button class="btn" style="margin-top: 24rpx" @click="change">更换</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const phone = ref('')
const code = ref('')
const oldPhone = ref('')
const oldCode = ref('')
const newPhone = ref('')
const newCode = ref('')
const hasPhone = computed(() => Boolean(auth.me?.profile?.phone))

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

async function sendCode(purpose, target) {
  try {
    await api.sendMeCode(purpose, target)
    toast('验证码已发送')
  } catch (e) {
    toast(e.message)
  }
}

// 合并成功时旧令牌已失效，换用返回的新令牌（IFC-071/072）
async function done(result) {
  if (result.merged && result.token) {
    auth.setAuth(result.token, null)
    toast('账号已合并')
  } else {
    toast('已完成')
  }
  await auth.fetchMe()
}

async function bind() {
  try {
    await done(await api.bindPhone(phone.value, code.value))
  } catch (e) {
    toast(e.message)
  }
}

async function change() {
  try {
    await done(await api.changePhone(oldPhone.value, newPhone.value, oldCode.value, newCode.value))
  } catch (e) {
    toast(e.message)
  }
}

onShow(async () => {
  try {
    await auth.fetchMe()
  } catch (e) {
    /* 未登录由 http 统一跳转 */
  }
})
</script>
