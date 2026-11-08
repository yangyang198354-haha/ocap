<template>
  <view>
    <view class="card" v-if="poll">
      <view class="title">{{ poll.title }}</view>
      <view class="muted">{{ poll.description }} · 截止 {{ poll.deadline }}</view>
      <view v-for="q in poll.questions || []" :key="q.id" style="margin-top: 24rpx">
        <view style="font-weight: 600">{{ q.title }}{{ q.required ? '（必答）' : '' }}</view>
        <radio-group v-if="q.qtype === 'AGREE_OPPOSE_ABSTAIN'" @change="(e) => choose(q.id, e.detail.value)">
          <label v-for="o in agreeOptions" :key="o.value" style="display: block; padding: 12rpx 0">
            <radio :value="o.value" style="transform: scale(.8)" />
            <text>{{ o.label }}</text>
          </label>
        </radio-group>
        <radio-group v-else-if="q.qtype === 'SINGLE'" @change="(e) => choose(q.id, e.detail.value)">
          <label v-for="o in q.options" :key="o" style="display: block; padding: 12rpx 0">
            <radio :value="o" style="transform: scale(.8)" />
            <text>{{ o }}</text>
          </label>
        </radio-group>
        <checkbox-group v-else-if="q.qtype === 'MULTI'" @change="(e) => choose(q.id, e.detail.value)">
          <label v-for="o in q.options" :key="o" style="display: block; padding: 12rpx 0">
            <checkbox :value="o" />
            <text>{{ o }}</text>
          </label>
        </checkbox-group>
        <radio-group v-else-if="q.qtype === 'SCORE'" @change="(e) => choose(q.id, e.detail.value)">
          <label v-for="n in [1, 2, 3, 4, 5]" :key="n" style="display: inline-block; padding: 12rpx 16rpx">
            <radio :value="String(n)" style="transform: scale(.8)" />
            <text>{{ n }}</text>
          </label>
        </radio-group>
        <textarea v-else @input="(e) => choose(q.id, e.detail.value)" style="border: 1px solid #e5e7eb; border-radius: 8rpx; padding: 16rpx; width: 100%" />
      </view>
      <button v-if="poll.status === 'OPEN' && poll.can_respond && !poll.my_response" class="btn" style="margin-top: 24rpx" @click="submit">提交</button>
      <view v-else-if="poll.my_response" class="muted" style="margin-top: 24rpx">你已提交</view>
      <button v-if="poll.status === 'CLOSED'" style="margin-top: 16rpx" @click="loadResult">查看结果</button>
      <view v-if="result" style="margin-top: 24rpx">
        <view v-for="row in result.questions || []" :key="row.id">
          <view style="font-weight: 600">{{ row.title }}</view>
          <template v-if="row.options">
            <view v-for="o in row.options" :key="o.value" class="muted">{{ o.value }}：{{ o.count }}（{{ o.percentage }}%）</view>
          </template>
          <view v-else-if="row.counts" class="muted">同意 {{ row.counts.AGREE }} · 反对 {{ row.counts.DISAGREE }} · 弃权 {{ row.counts.ABSTAIN }}</view>
          <view v-else-if="row.average !== undefined" class="muted">平均分 {{ row.average }}（{{ row.count }} 人）</view>
          <view v-else class="muted">共 {{ row.count }} 条文本回答</view>
        </view>
      </view>
    </view>
    <view class="card" v-else><view class="muted">投票不存在或无权查看</view></view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { api } from '@/utils/api'

const agreeOptions = [
  { value: 'AGREE', label: '同意' },
  { value: 'DISAGREE', label: '反对' },
  { value: 'ABSTAIN', label: '弃权' }
]
const poll = ref(null)
const result = ref(null)
const answers = reactive({})
const id = ref('')

function choose(questionId, value) {
  answers[questionId] = value
}

async function load() {
  try {
    poll.value = await api.poll(id.value)
    if (poll.value.results) result.value = poll.value.results
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function submit() {
  // 后端要求 { question_id, value }；多选题 value 为选项数组
  const body = Object.entries(answers)
    .filter(([, value]) => (Array.isArray(value) ? value.length : value !== '' && value != null))
    .map(([questionId, value]) => ({ question_id: Number(questionId), value }))
  try {
    await api.respond(id.value, body)
    uni.showToast({ title: '已提交', icon: 'none' })
    load()
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function loadResult() {
  try {
    result.value = (await api.pollResult(id.value)).results
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

onLoad((query) => {
  id.value = query.id
  load()
})
</script>
