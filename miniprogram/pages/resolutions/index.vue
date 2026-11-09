<template>
  <ThemeRoot>
  <view>
    <view class="card">
      <view class="title">业委会决议</view>
      <view class="muted">仅公开决议可在此查看；内部决议请登录后在 Web 端查看。</view>
    </view>
    <view v-if="!items.length" class="card">
      <view class="muted">暂无决议</view>
    </view>
    <view v-for="item in items" :key="item.id" class="card res-card" @click="open(item)">
      <view class="res-idx">{{ resNo(item.id) }}</view>
      <view class="row">
        <text class="res-title">{{ item.title }}</text>
        <StatusTag class="muted-gap" :status="item.status" />
      </view>
      <template v-if="item.vote_counts">
        <view class="vote-bar">
          <view class="vote-agree" :style="{ width: share(item).agreePct + '%' }" />
          <view class="vote-disagree" :style="{ width: share(item).disagreePct + '%' }" />
          <view class="vote-abstain" :style="{ width: share(item).abstainPct + '%' }" />
        </view>
        <view class="vote-legend">
          <text>同意 {{ share(item).agree }}</text>
          <text>反对 {{ share(item).disagree }}</text>
          <text>弃权 {{ share(item).abstain }}</text>
        </view>
      </template>
      <view v-else class="vote-legend"><text>{{ modeText(item.approval_mode) }}：由指定负责人审批</text></view>
      <view class="res-foot">
        <text>{{ (item.initiator?.labels || []).join('、') || '发起人' }}<text class="mode-tag">{{ modeText(item.approval_mode) }}</text></text>
        <text v-if="item.vote_deadline">截止 {{ String(item.vote_deadline).replace('T', ' ').slice(0, 16) }}</text>
      </view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import StatusTag from '@/components/StatusTag.vue'
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { voteShare } from '@/utils/voteShare'

const items = ref([])

// 卡片展示用：编号由 id 派生（接口无决议编号字段）；比例同 Web 的 voteShare
const resNo = (id) => `R-${String(id).padStart(4, '0')}`
const modeText = (mode) => (mode === 'HALF_MAJORITY' ? '半数同意' : mode === 'DESIGNATED' ? '指定负责人' : mode)
const share = (item) => voteShare(item.vote_counts)

async function load() {
  try {
    const data = await api.resolutions('public')
    items.value = data.results || data || []
  } catch (e) {
    items.value = []
  }
}

function open(item) {
  uni.navigateTo({ url: `/pages/resolutions/detail?id=${item.id}` })
}

onShow(load)
</script>
