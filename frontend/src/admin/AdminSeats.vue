<!-- MOD-160 / IFC-372：业委会席位（持有人分列、楼栋/单元/职位过滤、非 ACTIVE 默认折叠）
     口径（GR-B-001-F02）：status=ACTIVE 但未到任期开始的席位保留在主表并显示"待生效"标签 -->
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
      <!-- IFC-356 / Q-B18-33=A：仅提示、不禁用任何按钮 -->
      <p v-if="hint && hint.pending_bind > 0" class="muted seat-hint">
        当前待绑定 {{ hint.pending_bind }} 人，半数同意决议至少需 {{ hint.need_agree }} 票同意
      </p>
      <p v-if="hint && hint.pending_bind > 0 && hint.can_pass === false" class="error-text seat-hint">
        当前半数同意决议无法通过
      </p>
      <!-- REQ-FUNC-291：昵称/姓名/电话/专有部分搜索与业主清册一致；筛选区与主表共用列宽网格 -->
      <div class="seat-scroll">
        <div class="filter-grid">
          <div class="filter-cell">
            <el-input v-model="nicknameKeyword" placeholder="昵称" clearable @change="resetAndLoad" />
          </div>
          <div class="filter-cell">
            <el-input v-model="nameKeyword" placeholder="姓名" clearable @change="resetAndLoad" />
          </div>
          <div class="filter-cell">
            <el-input v-model="phoneKeyword" placeholder="电话" clearable maxlength="11"
                      :formatter="digitsOnly" :parser="digitsOnly" @change="resetAndLoad" />
          </div>
          <div class="filter-cell">
            <el-input v-model="unitKeyword" placeholder="专有部分" clearable @change="resetAndLoad" />
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
            <el-input v-model="roomKeyword" placeholder="房号" clearable @change="resetAndLoad" />
          </div>
          <div class="filter-cell" />
          <div class="filter-cell" />
          <div class="filter-cell">
            <el-select v-model="position" placeholder="职位" clearable @change="resetAndLoad">
              <el-option v-for="p in positions" :key="p.value" :label="p.label" :value="p.value" />
            </el-select>
          </div>
          <div class="filter-cell" />
          <div class="filter-cell" />
          <div class="filter-cell" />
          <div class="filter-cell" />
        </div>

        <el-table :data="seats" size="small" class="seat-table">
          <el-table-column label="昵称" min-width="100">
            <template #default="{ row }">
              <router-link v-if="row.user?.id" :to="`/users/${row.user.id}/profile`" class="user-link">{{ nicknameText(row) }}</router-link>
              <template v-else>{{ nicknameText(row) }}</template>
            </template>
          </el-table-column>
          <el-table-column label="姓名" min-width="80">
            <template #default="{ row }">{{ nameText(row) }}</template>
          </el-table-column>
          <el-table-column label="联系电话" min-width="120">
            <template #default="{ row }">{{ row.holder_detail?.phone || '-' }}</template>
          </el-table-column>
          <el-table-column label="专有部分坐落" min-width="180" show-overflow-tooltip>
            <template #default="{ row }">{{ unitText(row) }}</template>
          </el-table-column>
          <el-table-column label="楼栋" min-width="80">
            <template #default="{ row }">{{ row.holder_detail?.building || '-' }}</template>
          </el-table-column>
          <el-table-column label="单元" min-width="80">
            <template #default="{ row }">{{ row.holder_detail?.unit_no || '-' }}</template>
          </el-table-column>
          <el-table-column label="楼层" min-width="80">
            <template #default="{ row }">{{ row.holder_detail?.floor || '-' }}</template>
          </el-table-column>
          <el-table-column label="房号" min-width="80">
            <template #default="{ row }">{{ row.holder_detail?.room || '-' }}</template>
          </el-table-column>
          <el-table-column label="专有部分类型" min-width="100">
            <template #default="{ row }">{{ row.holder_detail?.unit_type || '-' }}</template>
          </el-table-column>
          <el-table-column label="面积" min-width="90">
            <template #default="{ row }">{{ row.holder_detail?.area ? `${row.holder_detail.area} ㎡` : '-' }}</template>
          </el-table-column>
          <el-table-column label="职位" min-width="90">
            <template #default="{ row }">{{ positionLabel(row.position) }}</template>
          </el-table-column>
          <el-table-column label="状态" min-width="110">
            <template #default="{ row }">
              {{ statusLabel('seat', row.status) }}
              <el-tag v-if="row.status === 'ACTIVE' && row.effective === false" size="small" type="warning">待生效</el-tag>
              <el-tag v-if="row.bind_state === 'PENDING_BIND'" size="small" type="warning">待绑定</el-tag>
              <el-tag v-if="row.bind_state === 'CONFLICT'" size="small" type="danger">待处理冲突</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="term_start" label="任期开始" min-width="90" />
          <el-table-column prop="term_end" label="任期结束" min-width="90" />
          <el-table-column label="操作" min-width="220" class-name="op-cell">
            <template #default="{ row }">
              <div v-if="row.status === 'ACTIVE'" class="op-actions">
                <el-select v-model="changeTo[row.id]" placeholder="变更为" size="small" style="width: 96px">
                  <el-option v-for="p in positions" :key="p.value" :label="p.label" :value="p.value" />
                </el-select>
                <el-button size="small" type="primary" plain :disabled="!changeTo[row.id]" @click="change(row)">变更职位</el-button>
                <el-button size="small" type="danger" plain @click="revoke(row)">撤销</el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>
      <PagerBar :total="total" :page="page" :page-size="pageSize" sizable
                @change="gotoPage" @update:page-size="changePageSize" />
    </div>
    <div class="card">
      <el-collapse v-model="openedEnded" @change="onEndedToggle">
        <el-collapse-item name="ended" :title="`资格失效 / 已结束（${endedTotal}）`">
          <el-empty v-if="!endedSeats.length" description="暂无记录" />
          <el-table v-else :data="endedSeats" size="small">
            <el-table-column label="昵称" min-width="110">
              <template #default="{ row }">{{ row.holder_detail?.nickname || '-' }}</template>
            </el-table-column>
            <el-table-column label="姓名" min-width="100">
              <template #default="{ row }">{{ row.holder_detail?.name || '-' }}</template>
            </el-table-column>
            <el-table-column label="电话" width="120">
              <template #default="{ row }">{{ row.holder_detail?.phone_masked || '-' }}</template>
            </el-table-column>
            <el-table-column label="专有部分坐落" min-width="160">
              <template #default="{ row }">{{ row.holder_detail?.unit_text || '-' }}</template>
            </el-table-column>
            <el-table-column label="楼栋" width="80">
              <template #default="{ row }">{{ row.holder_detail?.building || '-' }}</template>
            </el-table-column>
            <el-table-column label="单元" width="80">
              <template #default="{ row }">{{ row.holder_detail?.unit_no || '-' }}</template>
            </el-table-column>
            <el-table-column label="楼层" width="80">
              <template #default="{ row }">{{ row.holder_detail?.floor || '-' }}</template>
            </el-table-column>
            <el-table-column label="房号" width="80">
              <template #default="{ row }">{{ row.holder_detail?.room || '-' }}</template>
            </el-table-column>
            <el-table-column label="类型" width="100">
              <template #default="{ row }">{{ row.holder_detail?.unit_type || '-' }}</template>
            </el-table-column>
            <el-table-column label="面积" width="90">
              <template #default="{ row }">{{ row.holder_detail?.area ? `${row.holder_detail.area} ㎡` : '-' }}</template>
            </el-table-column>
            <el-table-column label="职位" width="100">
              <template #default="{ row }">{{ positionLabel(row.position) }}</template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">{{ statusLabel('seat', row.status) }}</template>
            </el-table-column>
            <el-table-column label="结束原因" min-width="130">
              <template #default="{ row }">{{ row.end_reason || '-' }}</template>
            </el-table-column>
            <el-table-column prop="term_end" label="任期结束" width="100" />
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </div>

    <el-dialog v-model="showCreate" title="赋予席位" width="480px">
      <SeatHolderPicker v-model="form.registry_owner_id" />
      <el-select v-model="form.position" style="width: 100%; margin-top: 8px">
        <el-option v-for="p in positions" :key="p.value" :label="p.label" :value="p.value" />
      </el-select>
      <el-date-picker v-model="form.term_start" type="date" value-format="YYYY-MM-DD" placeholder="任期开始（默认今天）" style="margin-top: 8px; width: 100%" />
      <p class="muted">任期结束日按“人数与任期”配置的任期月数推算，须晚于今天；开始日在将来的席位到开始日才生效。</p>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText } from '@/shared/format'
import { confirmDanger } from '@/shared/confirm'
import { statusLabel } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'
import SeatHolderPicker from './parts/SeatHolderPicker.vue'

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
// 兼容旧响应（无 holder_detail）：回退到 user / holder 字段（AC-258-01 既有展示）
const nicknameText = (row) => {
  const name = row.holder_detail?.nickname || row.user?.nickname || row.user?.account_no
  return name ? `${name}（#${row.user?.id}）` : '-'
}
const nameText = (row) => row.holder_detail?.name || row.holder?.owner_name || '-'
const unitText = (row) => row.holder_detail?.unit_text || row.holder?.unit_text || '-'

const position = ref('')
const building = ref('')
const unitNo = ref('')
const floor = ref('')
const nicknameKeyword = ref('')
const nameKeyword = ref('')
const phoneKeyword = ref('')
const unitKeyword = ref('')
const roomKeyword = ref('')
const buildingOptions = ref([])
const unitOptions = ref([])
const floorOptions = ref([])
const digitsOnly = (value) => String(value ?? '').replace(/\D/g, '')
const filters = computed(() => {
  const f = { bucket: 'active' }
  if (position.value) f.position = position.value
  if (building.value) f.building = building.value
  if (unitNo.value) f.unit_no = unitNo.value
  if (floor.value) f.floor = floor.value
  if (roomKeyword.value) f.room = roomKeyword.value
  if (nicknameKeyword.value) f.nickname = nicknameKeyword.value
  if (nameKeyword.value) f.name = nameKeyword.value
  if (phoneKeyword.value) f.phone = phoneKeyword.value
  if (unitKeyword.value) f.unit_keyword = unitKeyword.value
  return f
})
// AC-265-01：失效总数由 active 响应带回，折叠区标题在展开前即可显示条数
const endedTotal = ref(0)
const { items: seats, total, page, pageSize, reload, goto, resetAndLoad: pagingReset, setPageSize } = usePaging({
  fetch: async (params) => {
    const data = await admin.seats(params)
    if (data && data.ended_count !== undefined) endedTotal.value = data.ended_count
    return data
  },
  filters
})

// REQ-FUNC-283：切换每页条数后回到第 1 页，保留职位/楼栋/单元筛选
function changePageSize(n) {
  setPageSize(n).catch((e) => ElMessage.error(errorText(e)))
}
const config = reactive({})
const changeTo = reactive({})
const showCreate = ref(false)
const showConfig = ref(false)
const form = reactive({ registry_owner_id: null, position: 'MEMBER', term_start: '' })
const hint = ref(null)
const openedEnded = ref([])
const endedSeats = ref([])
let endedLoaded = false

async function loadOptions(buildingValue, unitValue = '') {
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
  unitOptions.value = building.value ? await loadOptions(building.value) : []
  resetAndLoad()
}

async function onUnitChange() {
  floor.value = ''
  floorOptions.value = unitNo.value ? await loadOptions(building.value, unitNo.value) : []
  resetAndLoad()
}

async function load() {
  buildingOptions.value = await loadOptions('')
  try {
    const [, configData] = await Promise.all([reload(), admin.committeeConfig()])
    Object.assign(config, configData)
    hint.value = configData?.half_majority_hint || null
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function resetAndLoad() {
  try {
    await pagingReset()
    if (openedEnded.value.includes('ended')) await loadEnded()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function loadEnded() {
  try {
    const data = await admin.seats({ ...filters.value, bucket: 'ended', page: 1, page_size: 50 })
    endedSeats.value = data.results || []
    endedTotal.value = data.count || 0
    endedLoaded = true
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function onEndedToggle(names) {
  if (names.includes('ended')) await loadEnded()
}

async function gotoPage(n) {
  try {
    await goto(n)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function create() {
  if (!form.registry_owner_id) return ElMessage.warning('请先选择专有部分与产权业主')
  try {
    const body = { registry_owner_id: form.registry_owner_id, position: form.position }
    if (form.term_start) body.term_start = form.term_start
    await admin.createSeat(body)
    showCreate.value = false
    form.registry_owner_id = null
    ElMessage.success('已赋予')
    load()
    if (endedLoaded) loadEnded()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function change(row) {
  try {
    await admin.updateSeat(row.id, { position: changeTo[row.id] })
    ElMessage.success('已变更')
    load()
    if (endedLoaded) loadEnded()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function revoke(row) {
  const name = row.holder_detail?.name || row.holder?.owner_name ||
    row.holder_detail?.nickname || row.user?.nickname || row.user?.account_no
  if (!(await confirmDanger('revokeSeat', { name }))) return
  try {
    await admin.deleteSeat(row.id)
    ElMessage.success('已撤销')
    load()
    if (endedLoaded) loadEnded()
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

<style scoped>
/* REQ-FUNC-287：筛选区与主表同宽，按 min-width 比例伸展；窄屏仅本容器横向滚动 */
.seat-scroll { overflow-x: auto; margin-top: 10px; }
.filter-grid {
  display: grid;
  grid-template-columns: 100fr 80fr 120fr 180fr 80fr 80fr 80fr 80fr 100fr 90fr 90fr 110fr 90fr 90fr 220fr;
  width: 100%;
  min-width: 1590px;
  margin-bottom: 12px;
}
.filter-cell {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  padding: 0 8px;
  box-sizing: border-box;
}
.filter-cell :deep(.el-input),
.filter-cell :deep(.el-select) { width: 100%; }
.seat-table { min-width: 1590px; }
.seat-table :deep(.cell) { padding: 0 8px; }
.op-actions { display: flex; align-items: center; gap: 2px; white-space: nowrap; }
.op-actions :deep(.el-button) { padding-left: 4px; padding-right: 4px; margin-left: 0; }
.user-link { color: var(--accent); text-decoration: none; }
.user-link:hover { text-decoration: underline; }
</style>
