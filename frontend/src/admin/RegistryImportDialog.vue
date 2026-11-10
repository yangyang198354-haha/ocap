<template>
  <el-dialog :model-value="modelValue" title="批量导入业主清册" width="720px"
             :close-on-click-modal="false" @update:model-value="close">
    <div class="row" style="justify-content: space-between; margin-bottom: 8px">
      <span class="muted">先下载模板，按列填写后上传；导入前可先预检。</span>
      <div class="row">
        <el-button size="small" @click="downloadTemplate('xlsx')">下载 xlsx 模板</el-button>
        <el-button size="small" @click="downloadTemplate('csv')">下载 csv 模板</el-button>
      </div>
    </div>

    <template v-if="spec">
      <el-descriptions :column="2" size="small" border style="margin-bottom: 12px">
        <el-descriptions-item label="支持文件">{{ (spec.file_types || []).join('、') }}</el-descriptions-item>
        <el-descriptions-item label="限制">
          不超过 {{ spec.max_file_mb }} MB、不超过 {{ spec.max_rows }} 行
        </el-descriptions-item>
        <el-descriptions-item label="Excel">{{ spec.excel_sheet_note }}</el-descriptions-item>
        <el-descriptions-item label="类型取值">
          {{ (spec.unit_types || []).map((item) => item.label).join('、') }}
        </el-descriptions-item>
      </el-descriptions>

      <el-table :data="spec.columns || []" size="small" style="margin-bottom: 12px">
        <el-table-column prop="name" label="列名" width="180" />
        <el-table-column prop="required" label="是否必填" width="120" />
        <el-table-column prop="allowed" label="允许取值" />
        <el-table-column prop="example" label="示例" width="120" />
      </el-table>

      <el-alert type="info" :closable="false" style="margin-bottom: 12px">
        <div v-for="note in spec.notes || []" :key="note">· {{ note }}</div>
        <div>· 示例：1栋 / 1单元 / 3 / 301 分 3 行填写张三、李四、王芳（王芳不填手机号）；车位填 车库 / 空单元 / 空楼层 / A-088 / 车位 / 12.50。</div>
      </el-alert>
    </template>

    <el-upload :auto-upload="false" :show-file-list="false" :on-change="pick" accept=".csv,.xlsx">
      <el-button :disabled="busy">选择文件</el-button>
    </el-upload>
    <div v-if="file" class="muted" style="margin-top: 8px">{{ file.name }}</div>

    <div v-if="preview" style="margin-top: 12px">
      <div>{{ formatImportResult(preview) }}（预检结果，尚未写入）</div>
      <div v-if="preview.errors && preview.errors.length" style="margin-top: 8px">
        <div class="muted">以下行不会写入，其余行将正常导入：</div>
        <el-table :data="preview.errors" size="small" max-height="240">
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="field" label="字段" width="150" />
          <el-table-column prop="reason" label="原因" />
        </el-table>
        <el-button size="small" style="margin-top: 8px" @click="downloadErrors(preview)">下载错误清单</el-button>
      </div>
      <div v-if="preview.changes && preview.changes.length" style="margin-top: 8px">
        <div class="muted">以下既有专有部分的类型/面积将被修改：</div>
        <div v-for="item in preview.changes" :key="item.specific_part" class="muted">
          {{ item.specific_part }}：{{ fieldsText(item.fields) }}
        </div>
      </div>
    </div>

    <div v-if="result" style="margin-top: 12px">
      <el-alert :type="result.failed ? 'warning' : 'success'" :closable="false" :title="formatImportResult(result)" />
      <div v-if="result.errors && result.errors.length" style="margin-top: 8px">
        <el-table :data="result.errors" size="small" max-height="240">
          <el-table-column prop="row" label="行号" width="80" />
          <el-table-column prop="field" label="字段" width="150" />
          <el-table-column prop="reason" label="原因" />
        </el-table>
        <el-button size="small" style="margin-top: 8px" @click="downloadErrors(result)">下载错误清单</el-button>
      </div>
      <div v-if="result.changes && result.changes.length" style="margin-top: 8px">
        <div class="muted">以下既有专有部分的类型/面积已修改：</div>
        <div v-for="item in result.changes" :key="item.specific_part" class="muted">
          {{ item.specific_part }}：{{ fieldsText(item.fields) }}
        </div>
      </div>
    </div>

    <div v-if="busy" class="muted" style="margin-top: 8px">正在处理，请稍候…（最长 60 秒）</div>

    <template #footer>
      <el-button :disabled="busy" @click="close">关闭</el-button>
      <el-button :disabled="!file || busy" @click="run(true)">预检</el-button>
      <el-button type="primary" :disabled="!preview || busy" @click="run(false)">确认导入</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import {
  downloadBlob,
  downloadText,
  errorsCsv,
  formatImportResult,
  importErrorMessage
} from './registryImport'

const props = defineProps({ modelValue: Boolean })
const emit = defineEmits(['update:modelValue', 'imported'])

const spec = ref(null)
const file = ref(null)
const preview = ref(null)
const result = ref(null)
const busy = ref(false)

watch(
  () => props.modelValue,
  async (open) => {
    if (!open) return
    file.value = null
    preview.value = null
    result.value = null
    if (!spec.value) {
      try {
        spec.value = await admin.importSpec()
      } catch (e) {
        ElMessage.error(importErrorMessage(e))
      }
    }
  }
)

function close() {
  if (!busy.value) emit('update:modelValue', false)
}

function pick(uploadFile) {
  const raw = uploadFile && uploadFile.raw
  if (!raw) return
  if (raw.size > 5 * 1024 * 1024) {
    ElMessage.error('文件超过 5 MB')
    return
  }
  file.value = raw
  preview.value = null
  result.value = null
}

async function run(dryRun) {
  if (!file.value) return
  busy.value = true
  try {
    const data = await admin.importRegistry(file.value, dryRun)
    if (dryRun) {
      preview.value = data
    } else {
      result.value = data
      preview.value = null
      ElMessage.success('导入完成')
      emit('imported', data)
    }
  } catch (e) {
    ElMessage.error(importErrorMessage(e))
  } finally {
    busy.value = false
  }
}

async function downloadTemplate(type) {
  try {
    const blob = await admin.importTemplate(type)
    downloadBlob(blob, `registry_import_template.${type}`)
  } catch (e) {
    ElMessage.error(importErrorMessage(e))
  }
}

function downloadErrors(payload) {
  downloadText('registry_import_errors.csv', errorsCsv(payload.errors))
}

function fieldsText(fields) {
  const labels = { unit_type: '类型', area: '面积' }
  return (fields || []).map((field) => labels[field] || field).join('、')
}
</script>
