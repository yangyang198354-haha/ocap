<template>
  <div class="page">
    <PageHead title="业主清册">
      <el-button @click="showImport = true">批量导入</el-button>
      <el-button type="primary" @click="openCreate">新增</el-button>
    </PageHead>

    <div class="card">
      <!-- REQ-FUNC-281/282：筛选区与表格同一滚动容器、共用列宽网格；面积列无筛选控件保留空位 -->
      <div class="registry-scroll">
        <div class="filter-grid">
          <div class="filter-cell">
            <el-input v-model="keyword" clearable placeholder="专有部分标识" @change="search" />
          </div>
          <div class="filter-cell">
            <el-select v-model="filters.building" filterable clearable placeholder="楼栋" no-data-text="暂无数据"
                       @change="onBuildingChange">
              <el-option v-for="item in buildingOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </div>
          <div class="filter-cell">
            <el-select v-model="filters.unit_no" filterable clearable placeholder="单元" no-data-text="暂无数据"
                       :disabled="!filters.building" @change="onUnitChange">
              <el-option v-for="item in unitNoOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </div>
          <div class="filter-cell">
            <el-select v-model="filters.floor" filterable clearable placeholder="楼层" no-data-text="暂无数据"
                       :disabled="!filters.unit_no" @change="search">
              <el-option v-for="item in floorOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </div>
          <div class="filter-cell">
            <el-input v-model="filters.room" clearable placeholder="房号" maxlength="32" @change="search" />
          </div>
          <div class="filter-cell">
            <el-select v-model="typeFilter" clearable placeholder="类型" no-data-text="暂无数据"
                       @change="search">
              <el-option label="全部类型" value="" />
              <el-option label="未登记类型" value="UNSET" />
              <el-option v-for="item in UNIT_TYPES" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </div>
          <div class="filter-cell" />
          <div class="filter-cell owner-cell">
            <el-input v-model="filters.owner_name" clearable placeholder="业主姓名" maxlength="64"
                      @change="search" />
            <el-input v-model="filters.owner_phone" clearable placeholder="业主电话" maxlength="11"
                      :formatter="digitsOnly" :parser="digitsOnly" @change="search" />
          </div>
          <div class="filter-cell action-cell">
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </div>
        <!-- MOD-151：楼栋/单元/楼层/房号四列服务端排序（升序与降序两态），其余列不可排序 -->
        <el-table ref="tableRef" :data="items" size="small" empty-text="暂无数据" class="registry-table"
                  style="width: 100%" @sort-change="onSort">
          <el-table-column prop="specific_part" label="专有部分" min-width="180" show-overflow-tooltip />
          <el-table-column class-name="data-number" prop="building" label="楼栋" min-width="100" sortable="custom" :sort-orders="SORT_ORDERS" />
          <el-table-column class-name="data-number" prop="unit_no" label="单元" min-width="100" sortable="custom" :sort-orders="SORT_ORDERS" />
          <el-table-column class-name="data-number" prop="floor" label="楼层" min-width="100" sortable="custom" :sort-orders="SORT_ORDERS" />
          <el-table-column class-name="data-number" prop="room" label="房号" min-width="100" sortable="custom" :sort-orders="SORT_ORDERS" />
          <el-table-column label="类型" min-width="120">
            <template #default="{ row }">{{ row.unit_type_label || '未登记' }}</template>
          </el-table-column>
          <el-table-column label="面积" min-width="100">
            <template #default="{ row }">{{ row.area ? `${row.area} ㎡` : '未登记' }}</template>
          </el-table-column>
          <el-table-column label="业主" min-width="240" show-overflow-tooltip>
            <template #default="{ row }">{{ ownersText(row.owners) }}</template>
          </el-table-column>
          <el-table-column label="操作" min-width="150">
            <template #default="{ row }">
              <span class="row-actions">
                <el-button size="small" @click="openEdit(row)">编辑</el-button>
                <el-button type="danger" size="small" @click="remove(row)">删除</el-button>
              </span>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <PagerBar :total="total" :page="page" :page-size="pageSize" sizable
                @change="go" @update:page-size="changePageSize" />
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
        <el-button type="danger" size="small" @click="ownerDrafts.splice(index, 1)">删除</el-button>
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
import PageHead from '@/shared/PageHead.vue'
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import PagerBar from '@/shared/PagerBar.vue'
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
const pageSize = ref(20)
const total = ref(0)
const keyword = ref('')
const typeFilter = ref('')
const filters = reactive({ building: '', unit_no: '', floor: '', room: '', owner_name: '', owner_phone: '' })
const buildingOptions = ref([])
const unitNoOptions = ref([])
const floorOptions = ref([])
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
      page_size: pageSize.value,
      q: keyword.value || undefined,
      unit_type: typeFilter.value || undefined,
      building: filters.building || undefined,
      unit_no: filters.unit_no || undefined,
      floor: filters.floor || undefined,
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

// 楼栋 → 单元 → 楼层逐级联动（/admin/registry/unit-options）
async function loadOptions(params) {
  try {
    const data = await admin.unitOptions(params)
    return (data.options || []).map((o) => o.value)
  } catch (e) {
    return []
  }
}

async function loadFilterOptions() {
  buildingOptions.value = await loadOptions({})
}

async function onBuildingChange() {
  filters.unit_no = ''
  filters.floor = ''
  floorOptions.value = []
  unitNoOptions.value = filters.building ? await loadOptions({ building: filters.building }) : []
  search()
}

async function onUnitChange() {
  filters.floor = ''
  floorOptions.value = filters.unit_no
    ? await loadOptions({ building: filters.building, unit_no: filters.unit_no })
    : []
  search()
}

function resetFilters() {
  keyword.value = ''
  typeFilter.value = ''
  Object.assign(filters, { building: '', unit_no: '', floor: '', room: '', owner_name: '', owner_phone: '' })
  unitNoOptions.value = []
  floorOptions.value = []
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

// REQ-FUNC-283：切换每页条数后回到第 1 页，保留筛选与排序
function changePageSize(n) {
  pageSize.value = n
  page.value = 1
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

<style scoped>
/* REQ-FUNC-281：筛选区与表格同宽，按 min-width 比例伸展；窄屏仅本容器横向滚动 */
.registry-scroll { overflow-x: auto; }
.filter-grid {
  display: grid;
  grid-template-columns: 180fr 100fr 100fr 100fr 100fr 120fr 100fr 240fr 150fr;
  width: 100%;
  min-width: 1190px;
  margin-bottom: 12px;
}
.filter-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  padding: 0 10px;
  box-sizing: border-box;
}
.filter-cell :deep(.el-input),
.filter-cell :deep(.el-select) { width: 100%; }
.owner-cell :deep(.el-input) { width: auto; flex: 1; min-width: 0; }
.action-cell :deep(.el-button) { width: 100%; }
.registry-table { min-width: 1190px; }
.row-actions { white-space: nowrap; }
</style>
