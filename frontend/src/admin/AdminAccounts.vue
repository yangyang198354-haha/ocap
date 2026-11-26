<template>
  <div class="page">
    <PageHead title="账户管理">
      <el-button type="primary" @click="openCreate">新建账户</el-button>
    </PageHead>
    <div class="card">
      <p class="muted">账户可停用不可删除；新建的账户余额从 0.00 开始，入账时默认使用默认账户，可改选其他启用账户。</p>
    </div>

    <div class="card">
      <el-table :data="accounts" size="small">
        <el-table-column prop="name" label="账户名称" min-width="180" />
        <el-table-column label="账户号" min-width="140">
          <template #default="{ row }">{{ row.account_no || '—' }}</template>
        </el-table-column>
        <el-table-column label="余额" width="120">
          <template #default="{ row }"><span class="mono">¥{{ row.balance }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'ENABLED' ? 'success' : 'info'">
              {{ row.status === 'ENABLED' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="默认" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" size="small" type="warning">默认</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <div class="row account-actions">
              <el-button size="small" @click="openEdit(row)">编辑</el-button>
              <el-button size="small" type="primary" plain :disabled="row.is_default" @click="setDefault(row)">设为默认</el-button>
              <el-button
                size="small"
                :type="row.status === 'ENABLED' ? 'danger' : 'success'"
                plain
                @click="toggleStatus(row)"
              >
                {{ row.status === 'ENABLED' ? '停用' : '启用' }}
              </el-button>
            </div>
          </template>
        </el-table-column>
      </el-table>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>

    <el-dialog v-model="dialogVisible" :title="editingId ? '编辑账户' : '新建账户'" width="480px">
      <div class="field-block">
        <span class="field-label">账户名称</span>
        <el-input v-model="form.name" maxlength="64" placeholder="如：第四届业主委员会基本账户" />
      </div>
      <div class="field-block">
        <span class="field-label">账户号</span>
        <el-input v-model="form.account_no" maxlength="32" placeholder="唯一账户号" />
      </div>
      <p v-if="formError" class="error-text">{{ formError }}</p>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { accountApi } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText } from '@/shared/format'
import { usePaging } from '@/shared/usePaging'

const { items: accounts, total, page, pageSize, reload, goto } = usePaging({
  fetch: (params) => accountApi.adminList(params)
})
const dialogVisible = ref(false)
const editingId = ref(null)
const saving = ref(false)
const formError = ref('')
const form = reactive({ name: '', account_no: '' })

async function load() {
  try {
    await reload()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function gotoPage(n) {
  try {
    await goto(n)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function openCreate() {
  editingId.value = null
  form.name = ''
  form.account_no = ''
  formError.value = ''
  dialogVisible.value = true
}

function openEdit(row) {
  editingId.value = row.id
  form.name = row.name
  form.account_no = row.account_no || ''
  formError.value = ''
  dialogVisible.value = true
}

async function save() {
  const name = form.name.trim()
  const accountNo = form.account_no.trim()
  if (!name) { formError.value = '请填写账户名称'; return }
  if (!accountNo) { formError.value = '请填写账户号'; return }
  saving.value = true
  formError.value = ''
  try {
    const body = { name, account_no: accountNo }
    if (editingId.value) await accountApi.update(editingId.value, body)
    else await accountApi.create(body)
    dialogVisible.value = false
    ElMessage.success('账户已保存')
    await load()
  } catch (e) {
    formError.value = errorText(e) || '保存失败'
  } finally {
    saving.value = false
  }
}

async function setDefault(row) {
  try {
    await accountApi.update(row.id, { is_default: true })
    ElMessage.success('已设为默认账户')
    await load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function toggleStatus(row) {
  try {
    await accountApi.update(row.id, { status: row.status === 'ENABLED' ? 'DISABLED' : 'ENABLED' })
    ElMessage.success(row.status === 'ENABLED' ? '账户已停用' : '账户已启用')
    await load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>

<style scoped>
.account-actions { gap: 6px; }
.account-actions :deep(.el-button + .el-button) { margin-left: 0; }
</style>
