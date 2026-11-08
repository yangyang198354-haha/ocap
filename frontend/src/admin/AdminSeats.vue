<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">业委会席位</h3>
        <el-button type="primary" @click="showCreate = true">赋予席位</el-button>
      </div>
      <p class="muted">配置：主任 {{ config.cap_chair || '-' }} 人、副主任 {{ config.cap_vice || '-' }} 人、委员 {{ config.cap_member || '-' }} 人；任期 {{ config.term_months || '-' }} 个月，可连任。</p>
      <el-button size="small" @click="editConfig">修改人数与任期</el-button>
    </div>
    <div class="card">
      <el-table :data="seats" size="small">
        <el-table-column prop="user_id" label="用户" width="100" />
        <el-table-column prop="position" label="职位" width="130" />
        <el-table-column prop="term_start" label="任期开始" width="130" />
        <el-table-column prop="term_end" label="任期结束" width="130" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" @click="change(row)">变更职位</el-button>
            <el-button size="small" type="danger" @click="revoke(row)">撤销</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showCreate" title="赋予席位" width="480px">
      <el-input v-model="form.user_id" placeholder="用户 ID" />
      <el-select v-model="form.position" style="width: 100%; margin-top: 8px">
        <el-option label="主任" value="CHAIR" />
        <el-option label="副主任" value="VICE_CHAIR" />
        <el-option label="委员" value="MEMBER" />
      </el-select>
      <el-input v-model="form.term_start" placeholder="任期开始 YYYY-MM-DD" style="margin-top: 8px" />
      <el-input v-model="form.term_end" placeholder="任期结束 YYYY-MM-DD" style="margin-top: 8px" />
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showConfig" title="人数与任期配置" width="480px">
      <el-input v-model.number="config.cap_chair" placeholder="主任人数" />
      <el-input v-model.number="config.cap_vice" placeholder="副主任人数" style="margin-top: 8px" />
      <el-input v-model.number="config.cap_member" placeholder="委员人数" style="margin-top: 8px" />
      <el-input v-model.number="config.term_months" placeholder="任期（月）" style="margin-top: 8px" />
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

const seats = ref([])
const config = reactive({ cap_chair: 1, cap_vice: 2, cap_member: 6, term_months: 36 })
const showCreate = ref(false)
const showConfig = ref(false)
const form = reactive({ user_id: '', position: 'MEMBER', term_start: '', term_end: '' })

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
    await admin.createSeat({ ...form, user_id: Number(form.user_id) })
    showCreate.value = false
    ElMessage.success('已赋予')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function change(row) {
  try {
    await admin.updateSeat(row.id, { position: row.position === 'MEMBER' ? 'CHAIR' : 'MEMBER' })
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

function editConfig() {
  showConfig.value = true
}

async function saveConfig() {
  try {
    await admin.updateCommitteeConfig({ ...config })
    showConfig.value = false
    ElMessage.success('已保存')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
