<!-- MOD-182：个人资料面板（昵称编辑 + 手机号/邮箱只读摘要；供“个人资料”页 Tab 使用） -->
<template>
  <view>
    <view class="card">
      <view class="title">个人资料</view>
      <input v-model="nickname" type="nickname" placeholder="昵称" class="field" />
      <button class="btn" style="margin-top: 24rpx" @click="save">保存</button>
      <view class="muted" style="margin-top: 16rpx">手机号：{{ phone || '未绑定' }}</view>
      <view class="muted">邮箱：{{ email || '未填写' }}</view>
    </view>
  </view>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api } from '@/utils/api'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const nickname = ref('')
const phone = ref('')
const email = ref('')

async function load() {
  try {
    await auth.fetchMe()
  } catch (e) {
    /* 未登录由 http 统一跳转 */
  }
  nickname.value = auth.me?.profile?.nickname || ''
  phone.value = auth.me?.profile?.phone || ''
  email.value = auth.me?.profile?.email || ''
}

async function save() {
  try {
    await api.updateProfile({ nickname: nickname.value })
    await auth.fetchMe().catch(() => null)
    uni.showToast({ title: '已保存', icon: 'none' })
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

onMounted(load)
</script>
