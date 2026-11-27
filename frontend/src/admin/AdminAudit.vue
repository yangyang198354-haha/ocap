<template>
  <div class="page">
    <PageHead :title="isLogs ? '审计日志' : '系统配置'" />
    <div v-if="!isLogs" class="card">
      <div class="row">
        <span>审计日志保留期限（月，≥6）</span>
        <el-input v-model="retention" style="max-width: 120px" />
        <el-button type="primary" @click="saveRetention">保存</el-button>
      </div>
    </div>
    <div v-if="isLogs" class="card">
      <div class="row">
        <el-input v-model="filters.action" placeholder="动作" style="max-width: 180px" @change="load" />
        <el-input v-model="filters.object_type" placeholder="对象类型" style="max-width: 180px" @change="load" />
      </div>
      <el-table :data="logs" size="small" style="margin-top: 10px">
        <el-table-column class-name="data-number" label="时间" width="180">
          <template #default="{ row }">{{ datetime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column label="主体" width="90">
          <template #default="{ row }">{{ textOf(AUDIT_ACTOR_TEXT, row.actor_type) }}</template>
        </el-table-column>
        <el-table-column prop="action" label="动作" min-width="170" />
        <el-table-column prop="object_type" label="对象" min-width="120" />
        <el-table-column class-name="data-number" prop="object_id" label="对象 ID" width="110" />
        <el-table-column label="结果" width="90">
          <template #default="{ row }">{{ textOf(AUDIT_RESULT_TEXT, row.result) }}</template>
        </el-table-column>
      </el-table>
      <div class="row" style="margin-top: 10px">
        <el-button :disabled="page <= 1" @click="go(page - 1)">上一页</el-button>
        <span class="muted">第 {{ page }} 页 / 共 {{ total }} 条</span>
        <el-button :disabled="logs.length < pageSize" @click="go(page + 1)">下一页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { datetime, errorText } from '@/shared/format'
import { textOf } from '@/shared/labels'
import { AUDIT_ACTOR_TEXT, AUDIT_RESULT_TEXT } from '@/shared/adminText'

// 分区由路由 props 决定（MOD-126 / IFC-324）：config 系统配置 / logs 审计日志
const props = defineProps({ section: { type: String, default: 'config' } })
const isLogs = computed(() => props.section === 'logs')
const retention = ref(24)
const logs = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const filters = reactive({ action: '', object_type: '' })

async function load() {
  try {
    const data = await admin.auditLogs({
      page: page.value,
      page_size: pageSize,
      action: filters.action || undefined,
      object_type: filters.object_type || undefined
    })
    logs.value = data.results || data || []
    total.value = data.count ?? logs.value.length
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function go(next) {
  page.value = next
  load()
}

async function loadConfig() {
  try {
    const data = await admin.systemConfig('audit.retention_months')
    retention.value = data.value ?? data
  } catch (e) {
    /* 使用默认值展示 */
  }
}

async function saveRetention() {
  try {
    await admin.updateSystemConfig('audit.retention_months', Number(retention.value))
    ElMessage.success('已保存')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

// 兄弟路由复用同一实例：切换分区时只请求该分区所需数据
function enterSection() {
  if (isLogs.value) load()
  else loadConfig()
}

watch(() => props.section, enterSection)
onMounted(enterSection)
</script>
