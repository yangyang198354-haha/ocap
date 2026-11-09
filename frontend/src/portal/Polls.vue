<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">投票 / 调查</h3>
        <el-button v-if="auth.isChairOrVice" type="primary" @click="showCreate = true">发起</el-button>
      </div>
      <p class="muted">截止后统一汇总；截止前任何人（含发起人）不可查看结果。</p>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无投票或调查" />
      <div v-for="item in items" :key="item.id" class="list-item">
        <router-link :to="`/polls/${item.id}`">{{ item.title }}</router-link>
        <span class="muted" style="margin-left: 8px">
          {{ item.kind === 'REP_VOTE' ? '业主代表投票' : '调查' }} · {{ item.status }} · 截止 {{ item.deadline }}
        </span>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="发起投票/调查" width="680px">
      <el-radio-group v-model="form.kind">
        <el-radio-button value="SURVEY">调查</el-radio-button>
        <el-radio-button value="REP_VOTE">业主代表投票</el-radio-button>
      </el-radio-group>
      <el-select v-if="form.kind === 'SURVEY'" v-model="form.survey_scope" placeholder="调查对象" style="margin-top: 10px; width: 100%">
        <el-option label="仅产权业主" value="OWNERS_ONLY" />
        <el-option label="产权业主和同住人" value="OWNERS_AND_RESIDENTS" />
      </el-select>
      <el-input v-model="form.title" placeholder="标题" maxlength="200" style="margin-top: 10px" />
      <el-input v-model="form.description" type="textarea" :rows="2" placeholder="说明（选填）" style="margin-top: 10px" />
      <el-date-picker v-model="form.deadline" type="datetime" placeholder="截止时间" style="margin-top: 10px; width: 100%" />
      <div v-for="(q, qi) in form.questions" :key="qi" class="list-item-top" style="margin-top: 12px">
        <el-input v-model="q.title" :placeholder="`题目 ${qi + 1}`" />
        <div class="row" style="margin-top: 6px">
          <el-select v-model="q.qtype" style="width: 200px" @change="resetOptions(q)">
            <el-option label="同意/反对/弃权" value="AGREE_OPPOSE_ABSTAIN" />
            <el-option label="单选" value="SINGLE" />
            <el-option label="多选" value="MULTI" />
            <el-option label="打分（1~5）" value="SCORE" />
            <el-option label="文本" value="TEXT" />
          </el-select>
          <el-checkbox v-model="q.required">必答</el-checkbox>
          <el-button v-if="form.questions.length > 1" size="small" @click="form.questions.splice(qi, 1)">删除题目</el-button>
        </div>
        <div v-if="['SINGLE', 'MULTI'].includes(q.qtype)" class="row" style="margin-top: 6px">
          <el-input v-for="(o, oi) in q.options" :key="oi" v-model="q.options[oi]" :placeholder="`选项 ${oi + 1}`" style="max-width: 160px" />
          <el-button size="small" :disabled="q.options.length >= 10" @click="q.options.push('')">加选项</el-button>
        </div>
      </div>
      <el-button style="margin-top: 10px" @click="addQuestion">加题目</el-button>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { pollApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const auth = useAuthStore()
const items = ref([])
const showCreate = ref(false)
const newQuestion = () => ({ title: '', qtype: 'AGREE_OPPOSE_ABSTAIN', required: true, options: ['', ''] })
const form = reactive({
  kind: 'SURVEY', survey_scope: 'OWNERS_AND_RESIDENTS', title: '', description: '', deadline: null,
  questions: [newQuestion()]
})

function addQuestion() {
  form.questions.push(newQuestion())
}

function resetOptions(q) {
  q.options = ['SINGLE', 'MULTI'].includes(q.qtype) ? ['', ''] : []
}

async function load() {
  try {
    const data = await pollApi.list()
    items.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function create() {
  const body = {
    kind: form.kind,
    title: form.title,
    description: form.description,
    deadline: form.deadline ? new Date(form.deadline).toISOString() : '',
    questions: form.questions.map((q) => ({
      title: q.title,
      qtype: q.qtype,
      required: q.required,
      options: ['SINGLE', 'MULTI'].includes(q.qtype) ? q.options.map((o) => o.trim()) : []
    }))
  }
  if (form.kind === 'SURVEY') body.survey_scope = form.survey_scope
  try {
    await pollApi.create(body)
    showCreate.value = false
    ElMessage.success('已创建')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(async () => {
  await auth.fetchMe().catch(() => null)
  load()
})
</script>
