<!-- MOD-161 / IFC-374：用户房屋关系（身份 + 楼栋/单元/楼层过滤 + 姓名/电话/专有部分搜索） -->
<template>
  <div class="page">
    <div class="card">
      <h3 class="title">用户房屋关系</h3>
      <!-- REQ-FUNC-284：筛选控件与表格列共用宽度网格（用户 160 / 专有部分 200 / 身份 120 / 认证时间 180 / 操作 140） -->
      <div class="membership-scroll">
        <div class="filter-grid">
          <div class="filter-cell">
            <el-input v-model="keyword" placeholder="姓名 / 手机号（后 4 位起）" clearable
                      @keyup.enter="resetAndLoad" @clear="resetAndLoad" />
          </div>
          <div class="filter-cell unit-cell">
            <el-input v-model="unitKeyword" placeholder="专有部分标识 / 户号" clearable class="span-2"
                      @keyup.enter="resetAndLoad" @clear="resetAndLoad" />
            <el-select v-model="building" placeholder="全部楼栋" clearable @change="onBuildingChange">
              <el-option v-for="o in buildingOptions" :key="o.value" :label="o.value" :value="o.value" />
            </el-select>
            <el-select v-model="unitNo" placeholder="全部单元" clearable :disabled="!building" @change="onUnitChange">
              <el-option v-for="o in unitOptions" :key="o.value" :label="o.value" :value="o.value" />
            </el-select>
            <el-select v-model="floor" placeholder="全部楼层" clearable :disabled="!unitNo" class="span-2"
                       @change="resetAndLoad">
              <el-option v-for="o in floorOptions" :key="o.value" :label="o.value" :value="o.value" />
            </el-select>
          </div>
          <div class="filter-cell">
            <el-select v-model="role" placeholder="全部身份" clearable @change="resetAndLoad">
              <el-option label="户主" value="HEAD" />
              <el-option label="产权业主" value="OWNER" />
              <el-option label="同住人" value="RESIDENT" />
            </el-select>
          </div>
          <div class="filter-cell" />
          <div class="filter-cell action-cell">
            <el-button type="primary" @click="resetAndLoad">搜索</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
        </div>
        <el-table :data="items" size="small" empty-text="暂无匹配记录" style="width: 800px">
          <el-table-column label="用户" width="160">
            <template #default="{ row }">
              <router-link :to="`/users/${row.user?.id}/profile`" class="user-link">
                {{ row.user?.nickname || row.user?.account_no }}（#{{ row.user?.id }}）
              </router-link>
            </template>
          </el-table-column>
          <el-table-column prop="specific_part" label="专有部分" width="200" />
          <el-table-column label="身份" width="120">
            <template #default="{ row }">{{ ROLE_LABELS[row.role] || row.role }}</template>
          </el-table-column>
          <el-table-column label="认证时间" width="180">
            <template #default="{ row }">{{ formatDateTime(row.certified_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="140">
            <template #default="{ row }">
              <el-button v-if="row.role !== 'RESIDENT'" size="small" type="danger" @click="revoke(row)">撤销认证</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <p class="muted">撤销产权业主认证时按接任规则处理户主：最早认证的其他产权业主接任，无则暂无户主。</p>
      <PagerBar :total="total" :page="page" :page-size="pageSize" sizable
                @change="gotoPage" @update:page-size="changePageSize" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText, formatDateTime } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { ROLE_LABELS } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'

const role = ref('')
const building = ref('')
const unitNo = ref('')
const floor = ref('')
const keyword = ref('')
const unitKeyword = ref('')
const buildingOptions = ref([])
const unitOptions = ref([])
const floorOptions = ref([])

const filters = computed(() => {
  const f = {}
  if (role.value) f.role = role.value
  if (building.value) f.building = building.value
  if (unitNo.value) f.unit_no = unitNo.value
  if (floor.value) f.floor = floor.value
  const unit = unitKeyword.value.trim()
  if (unit) f.unit_keyword = unit
  const kw = keyword.value.trim()
  if (kw) {
    if (/^\d{4,11}$/.test(kw)) f.phone = kw
    else f.q = kw
  }
  return f
})
const { items, total, page, pageSize, reload, goto, resetAndLoad: pagingReset, setPageSize } = usePaging({
  fetch: (params) => admin.memberships(params), filters
})

// REQ-FUNC-283：切换每页条数后回到第 1 页，保留筛选条件
function changePageSize(n) {
  setPageSize(n).catch((e) => ElMessage.error(errorText(e)))
}

function resetFilters() {
  role.value = ''
  building.value = ''
  unitNo.value = ''
  floor.value = ''
  keyword.value = ''
  unitKeyword.value = ''
  floorOptions.value = []
  resetAndLoad()
}

async function loadOptions(buildingValue, unitValue) {
  try {
    const data = await admin.unitOptions({
      ...(buildingValue ? { building: buildingValue } : {}),
      ...(unitValue ? { unit_no: unitValue } : {})
    })
    return data.options || []
  } catch (e) {
    return []
  }
}

async function onBuildingChange() {
  unitNo.value = ''
  floor.value = ''
  floorOptions.value = []
  unitOptions.value = building.value ? await loadOptions(building.value, '') : []
  resetAndLoad()
}

async function onUnitChange() {
  floor.value = ''
  floorOptions.value = unitNo.value ? await loadOptions(building.value, unitNo.value) : []
  resetAndLoad()
}

async function load() {
  buildingOptions.value = await loadOptions('', '')
  try {
    await reload()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function resetAndLoad() {
  try {
    await pagingReset()
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

async function revoke(row) {
  if (!(await confirmDanger('revokeMembership', { name: `${row.user?.nickname || row.user?.account_no} · ${row.specific_part}` }))) return
  try {
    const result = await admin.revokeMembership(row.user.id, row.unit_id)
    ElMessage.success(result.was_head && result.new_head_id ? '已撤销，户主已由最早认证的产权业主接任' : '已撤销')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>

<style scoped>
.membership-scroll { overflow-x: auto; }
.filter-grid {
  display: grid;
  grid-template-columns: 160px 200px 120px 180px 140px;
  width: 800px;
  margin-bottom: 12px;
}
.filter-cell {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  min-width: 0;
  padding: 0 12px;
  box-sizing: border-box;
}
.filter-cell :deep(.el-input),
.filter-cell :deep(.el-select) { width: 100%; }
.unit-cell {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
  align-content: start;
}
.unit-cell .span-2 { grid-column: span 2; }
.action-cell :deep(.el-button) { padding-inline: 8px; }
.user-link { color: var(--accent); text-decoration: none; }
.user-link:hover { text-decoration: underline; }
</style>
