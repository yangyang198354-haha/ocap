<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">业委会席位 / 业主代表</h3>
        <el-button type="primary" @click="showCreate = true">赋予席位</el-button>
      </div>
      <p class="muted">
        人数：主任 {{ config.cap_chair ?? '-' }}、副主任 {{ config.cap_vice ?? '-' }}、委员 {{ config.cap_member ?? '-' }}、业主代表 {{ config.cap_rep ?? '-' }}；
        任期（月）：主任 {{ config.term_months_chair ?? '-' }}、副主任 {{ config.term_months_vice ?? '-' }}、委员 {{ config.term_months_member ?? '-' }}、业主代表 {{ config.term_months_rep ?? '-' }}。
      </p>
      <el-button size="small" @click="showConfig = true">修改人数与任期</el-button>
    </div>
    <div class="card">
      <el-table :data="seats" size="small">
        <el-table-column label="用户" width="180">
          <template #default="{ row }">{{ row.user?.nickname || row.user?.account_no }}（#{{ row.user?.id }}）</template>
        </el-table-column>
        <el-table-column label="职位" width="130">
          <template #default="{ row }">{{ positionLabel(row.position) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="110" />
        <el-table-column prop="term_start" label="任期开始" width="130" />
        <el-table-column prop="term_end" label="任期结束" width="130" />
        <el-table-column label="操作" width="320">
          <template #default="{ row }">
            <template v-if="row.status === 'ACTIVE'">
              <el-select v-model="changeTo[row.id]" placeholder="变更为" size="small" style="width: 120px">
                <el-option v-for="p in positions" :key="p.value" :label="p.label" :value="p.value" />
              </el-select>
              <el-button size="small" :disabled="!changeTo[row.id]" @click="change(row)">变更职位</el-button>
              <el-button size="small" type="danger" @click="revoke(row)">撤销</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showCreate" title="赋予席位" width="480px">
      <el-input v-model="form.user_id" placeholder="用户 ID（须是有效产权业主）" />
      <el-select v-model="form.position" style="width: 100%; margin-top: 8px">
        <el-option v-for="p in positions" :key="p.value" :label="p.label" :value="p.value" />
      </el-select>
      <el-date-picker v-model="form.term_start" type="date" value-format="YYYY-MM-DD" placeholder="任期开始（默认今天）" style="margin-top: 8px; width: 100%" />
      <p class="muted">任期结束日按“人数与任期”配置的任期月数自动计算。</p>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showConfig" title="人数与任期配置" width="520px">
      <el-form label-width="120px">
        <el-form-item v-for="f in configFields" :key="f.key" :label="f.label">
          <el-input-number v-model="config[f.key]" :min="f.min" :max="f.max" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showConfig = false">取消</el-button>
        <el-button type="primary" @click="saveConfig">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'

const positions = [
  { value: 'CHAIR', label: '主任' },
  { value: 'VICE_CHAIR', label: '副主任' },
  { value: 'MEMBER', label: '委员' },
  { value: 'REPRESENTATIVE', label: '业主代表' }
]
const configFields = [
  { key: 'cap_chair', label: '主任人数', min: 0, max: 50 },
  { key: 'cap_vice', label: '副主任人数', min: 0, max: 50 },
  { key: 'cap_member', label: '委员人数', min: 0, max: 50 },
  { key: 'cap_rep', label: '业主代表人数', min: 0, max: 500 },
  { key: 'term_months_chair', label: '主任任期（月）', min: 1, max: 120 },
  { key: 'term_months_vice', label: '副主任任期（月）', min: 1, max: 120 },
  { key: 'term_months_member', label: '委员任期（月）', min: 1, max: 120 },
  { key: 'term_months_rep', label: '业主代表任期（月）', min: 1, max: 120 }
]
const positionLabel = (p) => positions.find((x) => x.value === p)?.label || p

const seats = ref([])
const config = reactive({})
const changeTo = reactive({})
const showCreate = ref(false)
const showConfig = ref(false)
const form = reactive({ user_id: '', position: 'MEMBER', term_start: '' })

async function load() {
  try {
    const [seatData, configData] = await Promise.all([admin.seats(), admin.committeeConfig()])
    seats.value = seatData.results || seatData || []
    Object.assign(config, configData)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function create() {
  try {
    const body = { user_id: Number(form.user_id), position: form.position }
    if (form.term_start) body.term_start = form.term_start
    await admin.createSeat(body)
    showCreate.value = false
    ElMessage.success('已赋予')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function change(row) {
  try {
    await admin.updateSeat(row.id, { position: changeTo[row.id] })
    ElMessage.success('已变更')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function revoke(row) {
  try {
    await admin.deleteSeat(row.id)
    ElMessage.success('已撤销')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function saveConfig() {
  try {
    const body = {}
    for (const f of configFields) body[f.key] = config[f.key]
    await admin.updateCommitteeConfig(body)
    showConfig.value = false
    ElMessage.success('已保存')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
