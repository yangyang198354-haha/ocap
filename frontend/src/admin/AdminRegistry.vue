<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">业主清册</h3>
        <div class="row">
          <el-button @click="showImport = true">批量导入</el-button>
          <el-button type="primary" @click="openCreate">新增</el-button>
        </div>
      </div>
      <!-- IFC-293：过滤器（REQ-FUNC-180/181/183）；占位文字与空状态全部中文 -->
      <div class="row" style="margin-top: 12px; flex-wrap: wrap">
        <el-input v-model="keyword" clearable placeholder="专有部分标识搜索" style="width: 200px" @change="search" />
        <el-select v-model="filters.building" filterable clearable placeholder="楼栋" no-data-text="暂无数据"
                   style="width: 120px" @change="search">
          <el-option v-for="item in buildingOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-select v-model="filters.unit_no" filterable clearable placeholder="单元" no-data-text="暂无数据"
                   style="width: 120px" @change="search">
          <el-option v-for="item in unitNoOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <el-input v-model="filters.room" clearable placeholder="户号" maxlength="32" style="width: 120px"
                  @change="search" />
        <el-select v-model="typeFilter" clearable placeholder="全部类型" no-data-text="暂无数据"
                   style="width: 130px" @change="search">
          <el-option label="全部类型" value="" />
          <el-option label="未登记类型" value="UNSET" />
          <el-option v-for="item in UNIT_TYPES" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-input v-model="filters.owner_name" clearable placeholder="产权业主姓名" maxlength="64"
                  style="width: 150px" @change="search" />
        <el-input v-model="filters.owner_phone" clearable placeholder="产权业主电话" maxlength="11"
                  :formatter="digitsOnly" :parser="digitsOnly" style="width: 150px" @change="search" />
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </div>

    <div class="card">
      <!-- MOD-151：楼栋/单元/楼层/房号四列服务端排序（升序与降序两态），其余列不可排序 -->
      <el-table ref="tableRef" :data="items" size="small" empty-text="暂无数据" @sort-change="onSort">
        <el-table-column prop="specific_part" label="专有部分" min-width="150" />
        <el-table-column prop="building" label="楼栋" width="80" sortable="custom" :sort-orders="SORT_ORDERS" />
        <el-table-column prop="unit_no" label="单元" width="80" sortable="custom" :sort-orders="SORT_ORDERS" />
        <el-table-column prop="floor" label="楼层" width="80" sortable="custom" :sort-orders="SORT_ORDERS" />
        <el-table-column prop="room" label="房号" width="90" sortable="custom" :sort-orders="SORT_ORDERS" />
        <el-table-column label="类型" width="100">
          <template #default="{ row }">{{ row.unit_type_label || '未登记' }}</template>
        </el-table-column>
        <el-table-column label="面积" width="110">
          <template #default="{ row }">{{ row.area ? `${row.area} ㎡` : '未登记' }}</template>
        </el-table-column>
        <el-table-column label="业主" min-width="220">
          <template #default="{ row }">{{ ownersText(row.owners) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
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

    <el-dialog v-model="showCreate" title="新增专有部分" width="460px">
      <el-input v-model="createForm.building" placeholder="楼栋（必填）" />
      <el-input v-model="createForm.unit_no" placeholder="单元（可空）" style="margin-top: 8px" />
      <el-input v-model="createForm.floor" placeholder="楼层（可空）" style="margin-top: 8px" />
      <el-input v-model="createForm.room" placeholder="户号（必填）" style="margin-top: 8px" />
      <el-select v-model="createForm.unit_type" placeholder="专有部分类型" style="margin-top: 8px; width: 100%">
        <el-option v-for="item in UNIT_TYPES" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-input v-model="createForm.area" placeholder="专有部分面积（平方米，车位必填）" style="margin-top: 8px" />
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="create">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showEdit" title="编辑专有部分" width="620px">
      <el-input v-model="editForm.building" placeholder="楼栋" />
      <el-input v-model="editForm.unit_no" placeholder="单元（可空）" style="margin-top: 8px" />
      <el-input v-model="editForm.floor" placeholder="楼层（可空）" style="margin-top: 8px" />
      <el-input v-model="editForm.room" placeholder="户号" style="margin-top: 8px" />
      <el-select v-model="editForm.unit_type" placeholder="专有部分类型" style="margin-top: 8px; width: 100%">
        <el-option v-for="item in UNIT_TYPES" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-input v-model="editForm.area" placeholder="专有部分面积（平方米，车位必填）" style="margin-top: 8px" />

      <div class="muted" style="margin-top: 12px">业主（姓名 + 手机号）</div>
      <div v-for="(owner, index) in ownerDrafts" :key="index" class="row" style="margin-top: 8px">
        <el-input v-model="owner.name" :placeholder="owner.id ? '业主姓名' : '业主姓名（必填）'" style="width: 160px" />
        <el-input v-model="owner.phonesText" placeholder="手机号，英文分号分隔" style="flex: 1" />
        <el-button size="small" @click="ownerDrafts.splice(index, 1)">删除</el-button>
      </div>
      <el-button size="small" style="margin-top: 8px" @click="addOwner">添加业主</el-button>

      <template #footer>
        <el-button @click="showEdit = false">取消</el-button>
        <el-button type="primary" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>

    <RegistryImportDialog v-model="showImport" @imported="load" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import RegistryImportDialog from './RegistryImportDialog.vue'

const UNIT_TYPES = [
  { value: 'RESIDENCE', label: '住宅' },
  { value: 'APARTMENT', label: '公寓' },
  { value: 'SHOP', label: '商铺' },
  { value: 'PARKING', label: '车位' },
  { value: 'OTHER', label: '其他' }
]

const SORT_ORDERS = ['ascending', 'descending']
const tableRef = ref(null)
// 排序状态：随翻页与过滤保持；无排序时不带 sort/order，服务端按默认升序
const sort = reactive({ prop: null, order: null })
const items = ref([])
const page = ref(1)
const pageSize = 20
const total = ref(0)
const keyword = ref('')
const typeFilter = ref('')
const filters = reactive({ building: '', unit_no: '', room: '', owner_name: '', owner_phone: '' })
const buildingOptions = ref([])
const unitNoOptions = ref([])
const showCreate = ref(false)
const showEdit = ref(false)
const showImport = ref(false)
const currentUnit = ref(null)
const ownerDrafts = ref([])
const createForm = reactive({ building: '', unit_no: '', floor: '', room: '', unit_type: '', area: '' })
const editForm = reactive({ building: '', unit_no: '', floor: '', room: '', unit_type: '', area: '' })

function ownersText(owners) {
  if (!owners || !owners.length) return '未登记'
  return owners
    .map((owner) => `${owner.name || '未登记姓名'}${owner.phones && owner.phones.length ? `（${owner.phones.join('/')}）` : ''}`)
    .join('；')
}

async function load() {
  try {
    const data = await admin.registryUnits({
      page: page.value,
      page_size: pageSize,
      q: keyword.value || undefined,
      unit_type: typeFilter.value || undefined,
      building: filters.building || undefined,
      unit_no: filters.unit_no || undefined,
      room: filters.room || undefined,
      owner_name: filters.owner_name || undefined,
      owner_phone: filters.owner_phone || undefined,
      sort: sort.prop && sort.order ? sort.prop : undefined,
      order: sort.prop && sort.order ? (sort.order === 'descending' ? 'desc' : 'asc') : undefined
    })
    items.value = data.results || data || []
    total.value = data.count ?? items.value.length
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function digitsOnly(value) {
  return String(value ?? '').replace(/\D/g, '')
}

async function loadFilterOptions() {
  try {
    const data = await admin.registryFilterOptions()
    buildingOptions.value = data.buildings || []
    unitNoOptions.value = data.unit_nos || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function resetFilters() {
  keyword.value = ''
  typeFilter.value = ''
  Object.assign(filters, { building: '', unit_no: '', room: '', owner_name: '', owner_phone: '' })
  Object.assign(sort, { prop: null, order: null }) // "重置"恢复默认升序并清除表头指示
  tableRef.value?.clearSort?.()
  search()
}

function onSort({ prop, order }) {
  Object.assign(sort, { prop: order ? prop : null, order: order || null })
  page.value = 1
  load()
}

function search() {
  page.value = 1
  load()
}

function go(next) {
  page.value = next
  load()
}

function openCreate() {
  Object.assign(createForm, { building: '', unit_no: '', floor: '', room: '', unit_type: '', area: '' })
  showCreate.value = true
}

async function create() {
  if (!createForm.building.trim() || !createForm.room.trim()) {
    ElMessage.error('请填写楼栋与户号')
    return
  }
  if (!createForm.unit_type) {
    ElMessage.error('请选择专有部分类型')
    return
  }
  if (createForm.unit_type === 'PARKING' && !createForm.area.trim()) {
    ElMessage.error('车位须填写专有部分面积')
    return
  }
  try {
    await admin.createRegistryUnit({
      building: createForm.building.trim(),
      unit_no: createForm.unit_no.trim(),
      floor: createForm.floor.trim(),
      room: createForm.room.trim(),
      unit_type: createForm.unit_type,
      area: createForm.area.trim() === '' ? null : createForm.area.trim()
    })
    ElMessage.success('已新增')
    showCreate.value = false
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function openEdit(row) {
  currentUnit.value = row
  Object.assign(editForm, {
    building: row.building,
    unit_no: row.unit_no,
    floor: row.floor,
    room: row.room,
    unit_type: row.unit_type || '',
    area: row.area || ''
  })
  ownerDrafts.value = (row.owners || []).map((owner) => ({
    id: owner.id,
    name: owner.name || '',
    phonesText: (owner.phones || []).join(';')
  }))
  showEdit.value = true
}

function addOwner() {
  ownerDrafts.value.push({ id: null, name: '', phonesText: '' })
}

async function saveEdit() {
  if (!editForm.building.trim() || !editForm.room.trim()) {
    ElMessage.error('请填写楼栋与户号')
    return
  }
  const payload = {
    building: editForm.building.trim(),
    unit_no: editForm.unit_no.trim(),
    floor: editForm.floor.trim(),
    room: editForm.room.trim()
  }
  // 既有记录类型/面积未登记时允许只改业主（AC-101-04）
  if (editForm.unit_type) payload.unit_type = editForm.unit_type
  if (String(editForm.area).trim() !== '') payload.area = String(editForm.area).trim()
  if (payload.unit_type === 'PARKING' && payload.area === undefined) {
    ElMessage.error('车位须填写专有部分面积')
    return
  }
  const owners = []
  for (const owner of ownerDrafts.value) {
    const name = owner.name.trim()
    if (!owner.id && !name) {
      ElMessage.error('新增业主必须填写姓名')
      return
    }
    const item = {
      name: name || null,
      phones: owner.phonesText.split(/[;；,，\s]+/).filter(Boolean)
    }
    if (owner.id) item.id = owner.id
    owners.push(item)
  }
  try {
    await admin.updateRegistryUnit(currentUnit.value.id, payload)
    await admin.registryOwners(currentUnit.value.id, owners)
    ElMessage.success('已保存')
    showEdit.value = false
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function remove(row) {
  if (!(await confirmDanger('deleteUnit', { name: row.specific_part }))) return
  try {
    await admin.deleteRegistryUnit(row.id)
    ElMessage.success('已删除')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(() => {
  load()
  loadFilterOptions()
})
</script>
