<template>
  <view>
    <view class="card" v-if="poll">
      <view class="title">{{ poll.title }}</view>
      <view class="muted">{{ poll.description }} · 截止 {{ poll.deadline }}</view>
      <view v-for="q in poll.questions || []" :key="q.id" style="margin-top: 24rpx">
        <view style="font-weight: 600">{{ q.text }}</view>
        <radio-group @change="(e) => choose(q.id, e)">
          <label v-for="o in q.options" :key="o.key" style="display: block; padding: 12rpx 0">
            <radio :value="o.key" style="transform: scale(.8)" />
            <text>{{ o.label }}</text>
          </label>
        </radio-group>
      </view>
      <button class="btn" style="margin-top: 24rpx" @click="submit">提交</button>
      <button style="margin-top: 16rpx" @click="loadResult">查看结果</button>
      <view v-if="result" style="margin-top: 24rpx">
        <view v-for="(row, idx) in result.questions || []" :key="idx">
          <view style="font-weight: 600">{{ row.text }}</view>
          <view v-for="o in row.options || []" :key="o.key" class="muted">{{ o.label }}：{{ o.count }}（{{ o.percent }}%）</view>
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

const poll = ref(null)
const result = ref(null)
const answers = reactive({})
const id = ref('')

function choose(questionId, event) {
  answers[questionId] = event.detail.value
}

async function load() {
  try {
    poll.value = await api.poll(id.value)
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

async function submit() {
  const body = Object.entries(answers).map(([questionId, optionKey]) => ({
    question_id: Number(questionId),
    option_key: optionKey
  }))
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
    result.value = await api.pollResult(id.value)
  } catch (e) {
    uni.showToast({ title: e.message, icon: 'none' })
  }
}

onLoad((query) => {
  id.value = query.id
  load()
})
</script>
