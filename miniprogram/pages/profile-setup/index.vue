<template>
  <ThemeRoot>
  <view class="card">
    <view class="title">完善资料</view>
    <button open-type="chooseAvatar" @chooseavatar="onChooseAvatar">
      <image v-if="avatarUrl" :src="avatarUrl" style="width: 120rpx; height: 120rpx; border-radius: 60rpx" />
      <text v-else>选择头像</text>
    </button>
    <input v-model="nickname" type="nickname" placeholder="昵称" class="field" style="margin-top: 24rpx" />
    <button class="btn" style="margin-top: 24rpx" @click="save">保存并进入</button>
    <button style="margin-top: 16rpx" @click="skip">稍后再说</button>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { ref } from 'vue'
import { api } from '@/utils/api'

const nickname = ref('')
const avatarUrl = ref('')

function onChooseAvatar(event) {
  avatarUrl.value = event.detail.avatarUrl
}

async function save() {
  try {
    await api.updateProfile({ nickname: nickname.value })
    uni.reLaunch({ url: '/pages/index/index' })
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

function skip() {
  uni.reLaunch({ url: '/pages/index/index' })
}
</script>
