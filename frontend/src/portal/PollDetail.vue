<template>
  <div class="page">
    <div class="card" v-if="poll">
      <h3 class="title">{{ poll.title }}</h3>
      <p class="muted">{{ poll.description }}</p>
      <p class="muted">状态：{{ poll.status }} · 截止：{{ poll.deadline }}</p>
      <div v-for="q in poll.questions || []" :key="q.id" style="margin-top: 14px">
        <strong>{{ q.text }}</strong>
        <el-radio-group v-model="answers[q.id]" style="display: block; margin-top: 8px">
          <el-radio v-for="o in q.options" :key="o.key" :label="o.key">{{ o.label }}</el-radio>
        </el-radio-group>
      </div>
      <div class="row" style="margin-top: 14px" v-if="poll.status === 'OPEN'">
        <el-button type="primary" @click="submit">一键提交</el-button>
        <el-button @click="loadResult">查看结果</el-button>
      </div>
      <div v-if="result" class="card" style="margin-top: 14px">
        <h4>结果</h4>
        <div v-for="(row, idx) in result.questions || []" :key="idx">
          <p>{{ row.text }}</p>
          <div v-for="o in row.options || []" :key="o.key" class="muted">
            {{ o.label }}：{{ o.count }}（{{ o.percent }}%）
          </div>
        </div>
      </div>
    </div>
    <div class="card" v-else><el-empty description="投票不存在或无权查看" /></div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { pollApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const route = useRoute()
const poll = ref(null)
const result = ref(null)
const answers = reactive({})

async function load() {
  try {
    poll.value = await pollApi.detail(route.params.id)
    if (poll.value.my_response) {
      Object.assign(answers, poll.value.my_response)
    }
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submit() {
  const body = Object.entries(answers).map(([questionId, optionKey]) => ({
    question_id: Number(questionId),
    option_key: optionKey
  }))
  try {
    await pollApi.respond(route.params.id, body)
    ElMessage.success('已提交')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function loadResult() {
  try {
    result.value = await pollApi.result(route.params.id)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
