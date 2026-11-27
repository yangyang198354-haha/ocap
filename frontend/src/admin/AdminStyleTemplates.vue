<!-- MOD-084 / REQ-FUNC-153：我的版式模板（自定义模板的新建、改名、编辑样式、删除；内置模板只读） -->
<template>
  <div class="page">
    <PageHead title="版式模板">
      <el-button type="primary" @click="openCreate">新建模板</el-button>
    </PageHead>
    <div class="card">
      <p class="muted">自定义模板保存后可在信息公开内容编辑器的模板列表中选用；被内容引用的模板不能删除；内置模板只读。</p>
    </div>
    <div class="card">
      <el-table :data="items" size="small">
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">{{ row.builtin ? '内置' : '自定义' }}</template>
        </el-table-column>
        <el-table-column label="被引用数" width="100">
          <template #default="{ row }">{{ row.builtin ? '—' : row.usage_count }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <template v-if="!row.builtin">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="remove(row)">删除</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showForm" :title="editingId ? '编辑模板' : '新建模板'" width="560px">
      <el-form label-width="96px">
        <el-form-item label="名称">
          <el-input v-model="form.name" maxlength="64" placeholder="模板名称" />
        </el-form-item>
        <el-form-item label="字体">
          <el-select v-model="form.tokens.font_family_key" style="width: 160px">
            <el-option v-for="o in FONT_OPTIONS" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item v-for="f in NUMERIC_FIELDS" :key="f.key" :label="f.label">
          <el-input-number v-model="form.tokens[f.key]" :min="f.min" :max="f.max" :step="f.step" />
        </el-form-item>
        <el-form-item v-for="f in COLOR_FIELDS" :key="f.key" :label="f.label">
          <el-color-picker v-model="form.tokens[f.key]" color-format="hex" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showForm = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'
import { COLOR_FIELDS, DEFAULT_TOKENS, FONT_OPTIONS, NUMERIC_FIELDS, mergeTokens } from './styleTemplate'

const items = ref([])
const showForm = ref(false)
const editingId = ref(null)
const form = reactive({ name: '', tokens: { ...DEFAULT_TOKENS } })

async function load() {
  try {
    items.value = (await admin.styleTemplates()) || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function openCreate() {
  editingId.value = null
  form.name = ''
  form.tokens = { ...DEFAULT_TOKENS }
  showForm.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.name = row.name
  form.tokens = mergeTokens(row.tokens)
  showForm.value = true
}

async function save() {
  if (!form.name.trim()) return ElMessage.warning('模板名称不能为空')
  const body = { name: form.name.trim(), tokens: { ...form.tokens } }
  try {
    if (editingId.value) await admin.updateStyleTemplate(editingId.value, body)
    else await admin.createStyleTemplate(body)
    showForm.value = false
    ElMessage.success('已保存')
    await load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function remove(row) {
  try {
    await ElMessageBox.confirm(`删除模板“${row.name}”后不可恢复，确认删除？`, '删除版式模板', {
      type: 'warning', confirmButtonText: '确认删除', confirmButtonClass: 'button-confirm-danger', cancelButtonText: '取消'
    })
  } catch (e) {
    return
  }
  try {
    await admin.deleteStyleTemplate(row.id)
    ElMessage.success('已删除')
    await load()
  } catch (e) {
    if (e?.code === 'STYLE_IN_USE') ElMessage.error(`被 ${e.details?.count ?? row.usage_count} 条内容引用，不能删除`)
    else ElMessage.error(errorText(e))
    await load()
  }
}

onMounted(load)
</script>
