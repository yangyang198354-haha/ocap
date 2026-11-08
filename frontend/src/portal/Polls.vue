<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">投票 / 调查</h3>
        <el-button v-if="isCommittee" type="primary" @click="showCreate = true">发起</el-button>
      </div>
      <p class="muted">截止后统一汇总；结果公开。</p>
    </div>
    <div class="card">
      <el-empty v-if="!items.length" description="暂无投票或调查" />
      <div v-for="item in items" :key="item.id" style="padding: 10px 0; border-bottom: 1px solid #f0f1f3">
        <router-link :to="`/polls/${item.id}`">{{ item.title }}</router-link>
        <span class="muted" style="margin-left: 8px">{{ item.status }} · 截止 {{ item.deadline }}</span>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="发起投票/调查" width="620px">
      <el-input v-model="form.title" placeholder="标题" maxlength="200" />
      <el-input v-model="form.description" type="textarea" :rows="2" placeholder="说明（选填）" style="margin-top: 10px" />
      <el-input v-model="form.deadline" placeholder="截止时间（YYYY-MM-DDTHH:mm:ss）" style="margin-top: 10px" />
      <div v-for="(q, qi) in form.questions" :key="qi" style="margin-top: 12px; border-top: 1px solid #f0f1f3; padding-top: 8px">
        <el-input v-model="q.text" :placeholder="`题目 ${qi + 1}`" />
        <div class="row" style="margin-top: 6px">
          <el-input v-for="(o, oi) in q.options" :key="oi" v-model="o.label" :placeholder="`选项 ${oi + 1}`" style="max-width: 160px" />
          <el-button size="small" @click="q.options.push({ key: `opt${q.options.length + 1}`, label: '' })">加选项</el-button>
        </div>
      </div>
      <el-button style="margin-top: 10px" @click="form.questions.push({ text: '', options: [{ key: 'yes', label: '同意' }, { key: 'no', label: '反对' }, { key: 'abstain', label: '弃权' }] })">
        加题目
      </el-button>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">提交</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { pollApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const auth = useAuthStore()
const isCommittee = computed(() => (auth.me?.identities || []).some((x) => ['委员', '主任', '副主任'].includes(x)))
const items = ref([])
const showCreate = ref(false)
const form = reactive({
  title: '', description: '', deadline: '',
  questions: [{ text: '', options: [{ key: 'yes', label: '同意' }, { key: 'no', label: '反对' }, { key: 'abstain', label: '弃权' }] }]
})

async function load() {
  try {
    const data = await pollApi.list()
    items.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function create() {
  try {
    await pollApi.create({
      title: form.title,
      description: form.description,
      deadline: form.deadline,
      questions: form.questions.map((q) => ({
        text: q.text,
        options: q.options.map((o, i) => ({ key: o.key || `opt${i + 1}`, label: o.label }))
      }))
    })
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
