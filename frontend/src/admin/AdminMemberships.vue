<!-- MOD-161 / IFC-374：用户房屋关系（身份 + 楼栋/单元/楼层过滤 + 姓名/电话/专有部分搜索） -->
<template>
  <div class="page">
    <PageHead title="用户房屋关系" />
    <div class="card">
      <!-- REQ-FUNC-292：管理后台展示实名与完整手机号；筛选区与表格列共用宽度网格 -->
      <div class="membership-scroll">
        <div class="filter-grid">
          <div class="filter-cell">
            <el-input v-model="keyword" placeholder="昵称 / 账号" clearable
                      @keyup.enter="resetAndLoad" @clear="resetAndLoad" />
          </div>
          <div class="filter-cell">
            <el-input v-model="nameKeyword" placeholder="实名" clearable
                      @keyup.enter="resetAndLoad" @clear="resetAndLoad" />
          </div>
          <div class="filter-cell">
            <el-input v-model="phoneKeyword" placeholder="手机号" clearable maxlength="11"
                      :formatter="digitsOnly" :parser="digitsOnly"
                      @keyup.enter="resetAndLoad" @clear="resetAndLoad" />
          </div>
          <div class="filter-cell">
            <el-input v-model="unitKeyword" placeholder="专有部分" clearable
                      @keyup.enter="resetAndLoad" @clear="resetAndLoad" />
          </div>
          <div class="filter-cell">
            <el-select v-model="building" placeholder="楼栋" clearable @change="onBuildingChange">
              <el-option v-for="o in buildingOptions" :key="o.value" :label="o.value" :value="o.value" />
            </el-select>
          </div>
          <div class="filter-cell">
            <el-select v-model="unitNo" placeholder="单元" clearable :disabled="!building" @change="onUnitChange">
              <el-option v-for="o in unitOptions" :key="o.value" :label="o.value" :value="o.value" />
            </el-select>
          </div>
          <div class="filter-cell">
            <el-select v-model="floor" placeholder="楼层" clearable :disabled="!unitNo" @change="resetAndLoad">
              <el-option v-for="o in floorOptions" :key="o.value" :label="o.value" :value="o.value" />
            </el-select>
          </div>
          <div class="filter-cell">
            <el-input v-model="roomKeyword" placeholder="房号" clearable
                      @keyup.enter="resetAndLoad" @clear="resetAndLoad" />
          </div>
          <div class="filter-cell" />
          <div class="filter-cell" />
          <div class="filter-cell">
            <el-select v-model="role" placeholder="身份" clearable @change="resetAndLoad">
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
        <el-table :data="items" size="small" empty-text="暂无匹配记录" class="membership-table">
          <el-table-column label="用户" min-width="160">
            <template #default="{ row }">
              <router-link :to="`/users/${row.user?.id}/profile`" class="user-link">
                {{ row.user?.nickname || row.user?.account_no }}（#{{ row.user?.id }}）
              </router-link>
            </template>
          </el-table-column>
          <el-table-column label="实名" min-width="110">
            <template #default="{ row }">{{ row.real_name || '-' }}</template>
          </el-table-column>
          <el-table-column label="手机号" min-width="130">
            <template #default="{ row }">{{ row.user?.phone || '-' }}</template>
          </el-table-column>
          <el-table-column prop="specific_part" label="专有部分" min-width="190" show-overflow-tooltip />
          <el-table-column label="楼栋" min-width="90">
            <template #default="{ row }">{{ row.building || '-' }}</template>
          </el-table-column>
          <el-table-column label="单元" min-width="90">
            <template #default="{ row }">{{ row.unit_no || '-' }}</template>
          </el-table-column>
          <el-table-column label="楼层" min-width="90">
            <template #default="{ row }">{{ row.floor || '-' }}</template>
          </el-table-column>
          <el-table-column label="房号" min-width="90">
            <template #default="{ row }">{{ row.room || '-' }}</template>
          </el-table-column>
          <el-table-column label="类型" min-width="110">
            <template #default="{ row }">{{ row.unit_type || '-' }}</template>
          </el-table-column>
          <el-table-column label="面积" min-width="90">
            <template #default="{ row }">{{ row.area ? `${row.area} ㎡` : '-' }}</template>
          </el-table-column>
          <el-table-column label="身份" min-width="100">
            <template #default="{ row }">{{ ROLE_LABELS[row.role] || row.role }}</template>
          </el-table-column>
          <el-table-column label="认证时间" min-width="160">
            <template #default="{ row }">{{ formatDateTime(row.certified_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" min-width="140">
            <template #default="{ row }">
              <el-button v-if="row.role !== 'RESIDENT'" class="op-btn" size="small" type="danger"
                         @click="revoke(row)">撤销认证</el-button>
              <!-- REQ-FUNC-293：管理员可移除同住人 -->
              <el-button v-else class="op-btn" size="small" type="danger" @click="removeResident(row)">移除同住人</el-button>
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
import PageHead from '@/shared/PageHead.vue'
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
const nameKeyword = ref('')
const phoneKeyword = ref('')
const unitKeyword = ref('')
const roomKeyword = ref('')
const buildingOptions = ref([])
const unitOptions = ref([])
const floorOptions = ref([])
const digitsOnly = (value) => String(value ?? '').replace(/\D/g, '')

const filters = computed(() => {
  const f = {}
  if (role.value) f.role = role.value
  if (building.value) f.building = building.value
  if (unitNo.value) f.unit_no = unitNo.value
  if (floor.value) f.floor = floor.value
  const unit = unitKeyword.value.trim()
  if (unit) f.unit_keyword = unit
  const room = roomKeyword.value.trim()
  if (room) f.room = room
  const kw = keyword.value.trim()
  if (kw) f.q = kw
  const name = nameKeyword.value.trim()
  if (name) f.name = name
  const phone = digitsOnly(phoneKeyword.value)
  if (phone) f.phone = phone
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
  nameKeyword.value = ''
  phoneKeyword.value = ''
  unitKeyword.value = ''
  roomKeyword.value = ''
  unitOptions.value = []
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

async function removeResident(row) {
  if (!(await confirmDanger('removeResident', { name: `${row.user?.nickname || row.user?.account_no} · ${row.specific_part}` }))) return
  try {
    await admin.revokeMembership(row.user.id, row.unit_id)
    ElMessage.success('已移除同住人')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>

<style scoped>
/* REQ-FUNC-292：13 列与筛选网格同宽，按 min-width 比例伸展；窄屏仅本容器横向滚动 */
.membership-scroll { overflow-x: auto; }
.filter-grid {
  display: grid;
  grid-template-columns: 160fr 110fr 130fr 190fr 90fr 90fr 90fr 90fr 110fr 90fr 100fr 160fr 140fr;
  width: 100%;
  min-width: 1550px;
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
.action-cell :deep(.el-button) { padding-inline: 8px; }
/* REQ-FUNC-293：操作列按钮等宽，避免 4/5 字文案宽度不一致 */
.op-btn { width: 96px; }
.membership-table { min-width: 1550px; }
.user-link { color: var(--accent); text-decoration: none; }
.user-link:hover { text-decoration: underline; }
</style>
