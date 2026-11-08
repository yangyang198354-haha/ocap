<template>
  <div class="page">
    <div class="card" v-if="poll">
      <h3 class="title">{{ poll.title }}</h3>
      <p class="muted">{{ poll.description }}</p>
      <p class="muted">
        {{ poll.kind === 'REP_VOTE' ? '业主代表投票' : '调查' }} · 状态：{{ poll.status }} · 截止：{{ poll.deadline }}
      </p>
      <div v-for="q in poll.questions || []" :key="q.id" style="margin-top: 14px">
        <strong>{{ q.title }}</strong>
        <span class="muted" style="margin-left: 6px">{{ q.required ? '必答' : '选答' }}</span>
        <div style="margin-top: 8px">
          <el-radio-group v-if="q.qtype === 'AGREE_OPPOSE_ABSTAIN'" v-model="answers[q.id]" :disabled="!canAnswer">
            <el-radio value="AGREE">同意</el-radio>
            <el-radio value="DISAGREE">反对</el-radio>
            <el-radio value="ABSTAIN">弃权</el-radio>
          </el-radio-group>
          <el-radio-group v-else-if="q.qtype === 'SINGLE'" v-model="answers[q.id]" :disabled="!canAnswer">
            <el-radio v-for="o in q.options" :key="o" :value="o">{{ o }}</el-radio>
          </el-radio-group>
          <el-checkbox-group v-else-if="q.qtype === 'MULTI'" v-model="answers[q.id]" :disabled="!canAnswer">
            <el-checkbox v-for="o in q.options" :key="o" :value="o">{{ o }}</el-checkbox>
          </el-checkbox-group>
          <el-rate v-else-if="q.qtype === 'SCORE'" v-model="answers[q.id]" :max="5" :disabled="!canAnswer" />
          <el-input v-else v-model="answers[q.id]" type="textarea" :rows="2" :disabled="!canAnswer" />
        </div>
      </div>
      <div class="row" style="margin-top: 14px">
        <el-button v-if="canAnswer" type="primary" @click="submit">一键提交</el-button>
        <span v-else-if="poll.my_response" class="muted">你已提交</span>
        <span v-else-if="poll.status === 'OPEN' && !poll.can_respond" class="muted">你不在本次参与范围内</span>
        <el-button v-if="poll.status === 'CLOSED'" @click="loadResult">查看结果</el-button>
      </div>
      <div v-if="result" class="card" style="margin-top: 14px">
        <h4>结果（参与 {{ result.responses }} / {{ result.participants }}）</h4>
        <div v-for="row in result.questions || []" :key="row.id" style="margin-bottom: 10px">
          <p style="margin: 4px 0">{{ row.title }}</p>
          <template v-if="row.options">
            <div v-for="o in row.options" :key="o.value" class="muted">{{ o.value }}：{{ o.count }}（{{ o.percentage }}%）</div>
          </template>
          <template v-else-if="row.counts">
            <div class="muted">同意 {{ row.counts.AGREE }} · 反对 {{ row.counts.DISAGREE }} · 弃权 {{ row.counts.ABSTAIN }}</div>
            <div v-if="row.denominator" class="muted">分母 {{ row.denominator }}，{{ row.passed ? '通过' : '未通过' }}</div>
          </template>
          <div v-else-if="row.average !== undefined" class="muted">平均分 {{ row.average }}（{{ row.count }} 人）</div>
          <div v-else class="muted">共 {{ row.count }} 条文本回答</div>
        </div>
      </div>
    </div>
    <div class="card" v-else><el-empty description="投票不存在或无权查看" /></div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { pollApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const route = useRoute()
const poll = ref(null)
const result = ref(null)
const answers = reactive({})

const canAnswer = computed(() => poll.value?.status === 'OPEN' && poll.value?.can_respond && !poll.value?.my_response)

async function load() {
  try {
    poll.value = await pollApi.detail(route.params.id)
    for (const q of poll.value.questions || []) {
      if (!(q.id in answers)) answers[q.id] = q.qtype === 'MULTI' ? [] : q.qtype === 'SCORE' ? 0 : ''
    }
    for (const a of poll.value.my_response || []) {
      const q = poll.value.questions.find((x) => x.id === a.question_id)
      answers[a.question_id] = q?.qtype === 'MULTI' ? a.value.split(',') : q?.qtype === 'SCORE' ? Number(a.value) : a.value
    }
    if (poll.value.results) result.value = poll.value.results
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submit() {
  const body = []
  for (const q of poll.value.questions) {
    const value = answers[q.id]
    const empty = Array.isArray(value) ? !value.length : value === '' || value === 0 || value == null
    if (empty) continue
    body.push({ question_id: q.id, value: q.qtype === 'SCORE' ? String(value) : value })
  }
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
    const data = await pollApi.result(route.params.id)
    result.value = data.results
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
