<template>
  <div class="page">
    <PageHead title="AI 服务配置" :description="isPrompts ? '提示词模板' : '模型与生成服务'" />
    <div>
      <div v-if="!isPrompts">
        <el-card v-for="item in services" :key="item.service_type" style="margin-bottom: 12px">
          <div class="row" style="justify-content: space-between">
            <strong>{{ item.label }}</strong>
            <div class="row">
              <el-tag v-if="item.last_test_ok === true" type="success">测试成功</el-tag>
              <el-tag v-else-if="item.last_test_ok === false" type="danger">测试失败</el-tag>
              <el-tag v-else type="info">未测试</el-tag>
              <el-button v-if="item.testable" size="small" @click="test(item)">测试连通</el-button>
            </div>
          </div>
          <div class="row" style="margin-top: 8px">
            <el-input v-model="item.params.model" placeholder="模型名" style="width: 260px" />
            <el-checkbox v-for="key in item.secret_fields" :key="key" disabled :model-value="item.secret_saved[key]">
              已保存 {{ key }}
            </el-checkbox>
          </div>
          <div class="row" style="margin-top: 8px">
            <el-input v-for="key in item.secret_fields" :key="`i-${key}`" v-model="item._secrets[key]"
                      :placeholder="`新的 ${key}（留空则不变）`" style="width: 240px" show-password />
            <el-button size="small" type="primary" @click="save(item)">保存</el-button>
          </div>
        </el-card>
      </div>
      <div v-else>
        <div class="row" style="margin-bottom: 12px">
          <el-input v-model="newPrompt.name" placeholder="名称" style="width: 200px" />
          <el-input v-model="newPrompt.prompt" placeholder="提示词" style="width: 420px" />
          <el-button @click="createPrompt">新增</el-button>
        </div>
        <el-table :data="prompts" border>
          <el-table-column prop="name" label="名称" width="180" />
          <el-table-column prop="prompt" label="提示词" />
          <el-table-column label="操作" width="160">
            <template #default="{ row }">
              <el-button size="small" @click="editPrompt(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="deletePrompt(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'

// 分区由路由 props 决定（MOD-126 / IFC-324）：models 模型与生成服务 / prompts 提示词模板
const props = defineProps({ section: { type: String, default: 'models' } })
const isPrompts = computed(() => props.section === 'prompts')
const services = ref([])
const prompts = ref([])
const newPrompt = reactive({ name: '', prompt: '' })

// 只请求当前分区所需数据（兄弟路由复用同一实例）
async function load() {
  if (isPrompts.value) {
    prompts.value = await admin.promptTemplates()
  } else {
    services.value = (await admin.contentServices()).map((item) => ({ ...item, _secrets: {} }))
  }
}
async function save(item) {
  const payload = { params: item.params }
  const secrets = Object.fromEntries(Object.entries(item._secrets).filter(([, value]) => value))
  if (Object.keys(secrets).length) payload.secrets = secrets
  try {
    await admin.saveContentService(item.service_type, payload)
    ElMessage.success('已保存')
    await load()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  }
}
async function test(item) {
  try {
    const result = await admin.testContentService(item.service_type)
    ElMessage[result.ok ? 'success' : 'error'](result.ok ? '测试成功' : `测试失败：${result.error_code}`)
    await load()
  } catch (err) {
    ElMessage.error(err.message || '测试失败')
  }
}
async function createPrompt() {
  try {
    await admin.createPromptTemplate({ name: newPrompt.name, prompt: newPrompt.prompt })
    newPrompt.name = ''
    newPrompt.prompt = ''
    prompts.value = await admin.promptTemplates()
  } catch (err) {
    ElMessage.error(err.message || '新增失败')
  }
}
async function editPrompt(row) {
  try {
    const { value } = await ElMessageBox.prompt('新的提示词', row.name, { inputValue: row.prompt })
    await admin.updatePromptTemplate(row.id, { prompt: value })
    prompts.value = await admin.promptTemplates()
  } catch { /* cancelled */ }
}
async function deletePrompt(row) {
  await admin.deletePromptTemplate(row.id)
  prompts.value = await admin.promptTemplates()
}
watch(() => props.section, load)
onMounted(load)
</script>
