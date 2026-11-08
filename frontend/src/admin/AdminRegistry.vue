<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">业主清册</h3>
        <div class="row">
          <el-input v-model="keyword" placeholder="楼栋/房号搜索" style="width: 200px" @change="load" />
          <el-upload :show-file-list="false" :http-request="importFile" accept=".csv,.xlsx">
            <el-button>批量导入</el-button>
          </el-upload>
          <el-button type="primary" @click="showCreate = true">新增</el-button>
        </div>
      </div>
    </div>
    <div class="card">
      <el-table :data="items" size="small">
        <el-table-column prop="specific_part" label="专有部分" min-width="160" />
        <el-table-column prop="building" label="楼栋" width="80" />
        <el-table-column prop="unit_no" label="单元" width="80" />
        <el-table-column prop="floor" label="楼层" width="80" />
        <el-table-column prop="room" label="房号" width="90" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editPhones(row)">登记手机号</el-button>
            <el-button size="small" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="row" style="margin-top: 12px">
        <el-button :disabled="page <= 1" @click="go(page - 1)">上一页</el-button>
        <span class="muted">第 {{ page }} 页 / 共 {{ total }} 条</span>
        <el-button :disabled="items.length < pageSize" @click="go(page + 1)">下一页</el-button>
      </div>
    </div>

    <el-dialog v-model="showCreate" title="新增专有部分" width="420px">
      <el-input v-model="form.building" placeholder="楼栋" />
      <el-input v-model="form.unit_no" placeholder="单元" style="margin-top: 8px" />
      <el-input v-model="form.floor" placeholder="楼层" style="margin-top: 8px" />
      <el-input v-model="form.room" placeholder="房号" style="margin-top: 8px" />
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showPhones" title="登记手机号" width="480px">
      <el-input v-model="phonesText" type="textarea" :rows="4" placeholder="每行一个手机号" />
      <template #footer>
        <el-button @click="showPhones = false">取消</el-button>
        <el-button type="primary" @click="savePhones">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'

const items = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const keyword = ref('')
const showCreate = ref(false)
const showPhones = ref(false)
const phonesText = ref('')
const currentUnit = ref(null)
const form = reactive({ building: '', unit_no: '', floor: '', room: '' })

async function load() {
  try {
    const data = await admin.registryUnits({ page: page.value, page_size: pageSize, q: keyword.value || undefined })
    items.value = data.results || data || []
    total.value = data.count ?? items.value.length
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function go(next) {
  page.value = next
  load()
}

async function create() {
  try {
    await admin.createRegistryUnit({ ...form })
    ElMessage.success('已新增')
    showCreate.value = false
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function importFile({ file }) {
  try {
    const result = await admin.importRegistry(file)
    ElMessage.success(`导入完成：${JSON.stringify(result)}`)
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function editPhones(row) {
  currentUnit.value = row
  phonesText.value = (row.phones || []).join('\n')
  showPhones.value = true
}

async function savePhones() {
  try {
    const phones = phonesText.value.split('\n').map((x) => x.trim()).filter(Boolean)
    await admin.registryUnitPhones(currentUnit.value.id, phones)
    ElMessage.success('已保存')
    showPhones.value = false
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function remove(row) {
  try {
    await admin.deleteRegistryUnit(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
