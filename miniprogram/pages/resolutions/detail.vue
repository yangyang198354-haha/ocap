<template>
  <ThemeRoot>
  <view>
    <view class="card" v-if="item">
      <view class="title">{{ item.title }}</view>
      <view class="muted"><StatusTag :status="item.status" /> · {{ item.approval_mode }}</view>
      <view style="margin-top: 16rpx; white-space: pre-wrap">{{ item.content }}</view>
      <view v-if="item.status === 'PENDING' && item.approval_mode === 'HALF_MAJORITY'" class="row" style="margin-top: 24rpx">
        <button size="mini" @click="vote('AGREE')">同意</button>
        <button size="mini" @click="vote('DISAGREE')">反对</button>
        <button size="mini" @click="vote('ABSTAIN')">弃权</button>
      </view>
    </view>
    <view class="card" v-else>
      <view class="muted">决议不存在或无权查看</view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import StatusTag from '@/components/StatusTag.vue'
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '@/utils/api'

const item = ref(null)
const id = ref('')

async function load() {
  try {
    item.value = await api.resolution(id.value)
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function vote(choice) {
  try {
    await api.vote(id.value, choice)
    uni.showToast({ title: '已提交', icon: 'none' })
    load()
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

onLoad((query) => {
  id.value = query.id
  load()
})
</script>
