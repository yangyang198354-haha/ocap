<template>
  <div class="page">
    <div class="card">
      <h3 class="title">业主清册认证</h3>
      <p class="muted">选择你的专有部分。清册登记手机号与当前手机号一致时可立即认证为产权业主；首位认证者为户主。</p>
      <div class="row">
        <el-select v-model="picked.building" placeholder="楼栋" @change="onBuildingChange">
          <el-option v-for="b in buildingOptions" :key="b.value" :label="b.value" :value="b.value" />
        </el-select>
        <el-select v-if="visibility.unit" v-model="picked.unit_no" placeholder="单元" @change="onUnitChange">
          <el-option v-for="u in unitOptions" :key="u.value" :label="u.label || u.value" :value="u.value" />
        </el-select>
        <el-select v-if="visibility.floor" v-model="picked.floor" placeholder="楼层" @change="onFloorChange">
          <el-option v-for="f in floorOptions" :key="f.value" :label="f.label || f.value" :value="f.value" />
        </el-select>
        <el-select v-if="visibility.room" v-model="picked.unitId" placeholder="户号">
          <el-option v-for="r in roomOptions" :key="r.unit_id" :label="r.label || r.value" :value="r.unit_id" />
        </el-select>
        <el-button type="primary" :disabled="!picked.unitId" @click="certify">认证</el-button>
      </div>
      <p v-for="tip in skippedTips" :key="tip" class="muted">{{ tip }}</p>
      <p v-if="picked.unitId" class="muted">{{ selectedUnitText }}</p>
    </div>

    <div class="card">
      <h3 class="title">认证申诉</h3>
      <p class="muted">清册手机号与当前手机号不一致时，可上传产权证明提交申诉，由管理员审核。</p>
      <div class="row" style="margin-top: 10px">
        <el-upload :show-file-list="false" :http-request="uploadProof" accept="image/*">
          <el-button>上传产权证明</el-button>
        </el-upload>
        <span class="muted" v-if="appeal.attachmentId">已上传</span>
        <el-button type="primary" :disabled="!picked.unitId" @click="submitAppeal">提交申诉</el-button>
      </div>
    </div>

    <div class="card">
      <h3 class="title">同住人</h3>
      <p class="muted">无产权业主时不允许申请同住人；由户主审批。</p>
      <div class="row">
        <el-input v-model="resident.unitId" placeholder="专有部分 ID" style="max-width: 160px" />
        <el-input v-model="resident.note" placeholder="说明（选填）" style="max-width: 260px" />
        <el-button @click="applyResident">申请成为同住人</el-button>
        <el-button @click="loadToReview">查看待我审批</el-button>
      </div>
      <div v-for="item in toReview" :key="item.id" class="row list-item-top">
        <span>{{ item.applicant?.nickname || item.applicant_id }} → {{ item.unit?.specific_part || item.unit_id }}</span>
        <el-button size="small" @click="decideResident(item.id, 'APPROVE')">通过</el-button>
        <el-button size="small" @click="decideResident(item.id, 'REJECT')">拒绝</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { attachmentApi, unitApi } from '@/shared/api'
import { errorText } from '@/shared/format'

const buildingOptions = ref([])
const unitOptions = ref([])
const floorOptions = ref([])
const roomOptions = ref([])
const skippedTips = ref([])
const visibility = reactive({ unit: false, floor: false, room: false })
const picked = reactive({ building: null, unit_no: null, floor: null, unitId: null })
const appeal = reactive({ attachmentId: null })
const resident = reactive({ unitId: '', note: '' })
const toReview = ref([])

const selectedUnit = computed(() => roomOptions.value.find((item) => item.unit_id === picked.unitId) || null)
const selectedUnitText = computed(() => {
  if (!selectedUnit.value) return ''
  const parts = [selectedUnit.value.unit_type_label || '类型未登记']
  parts.push(selectedUnit.value.area ? `${selectedUnit.value.area} ㎡` : '面积未登记')
  return `${parts.join(' · ')}；若该户未登记你的手机号，请改用下方产权申诉。`
})

async function loadOptions(params) {
  try {
    const data = await unitApi.options(params)
    return data
  } catch (e) {
    ElMessage.error(errorText(e))
    return {}
  }
}

async function loadBuildings() {
  const data = await loadOptions({})
  buildingOptions.value = data.options || []
}

function resetBelow(level) {
  if (level === 'building') {
    picked.unit_no = null
    picked.floor = null
    visibility.unit = false
    visibility.floor = false
    unitOptions.value = []
    floorOptions.value = []
    skippedTips.value = []
  }
  if (level === 'unit') {
    picked.floor = null
    visibility.floor = false
    floorOptions.value = []
  }
  picked.unitId = null
  visibility.room = false
  roomOptions.value = []
}

async function onBuildingChange() {
  resetBelow('building')
  if (picked.building === null) return
  await applyLevel(await loadOptions({ building: picked.building }), 'unit')
}

async function onUnitChange() {
  resetBelow('unit')
  if (picked.unit_no === null) return
  await applyLevel(await loadOptions({ building: picked.building, unit_no: picked.unit_no }), 'floor')
}

async function onFloorChange() {
  resetBelow('floor')
  if (picked.floor === null) return
  showRooms(await loadOptions({ building: picked.building, unit_no: picked.unit_no, floor: picked.floor }))
}

async function applyLevel(data, stage) {
  if (data.level === 'room') {
    showRooms(data)
    return
  }
  if (stage === 'unit') {
    if (data.level === 'unit_no') {
      visibility.unit = true
      unitOptions.value = data.has_empty
        ? [{ value: '', label: '未划分单元' }, ...(data.options || [])]
        : (data.options || [])
      return
    }
    picked.unit_no = ''
    skippedTips.value = ['该楼栋没有分单元，已自动跳过']
    await loadFloorsAfterSkip()
    return
  }
  if (data.level === 'floor') {
    visibility.floor = true
    floorOptions.value = data.has_empty
      ? [{ value: '', label: '未划分楼层' }, ...(data.options || [])]
      : (data.options || [])
    return
  }
  picked.floor = ''
  skippedTips.value = [...skippedTips.value, '该单元没有分楼层，已自动跳过']
  showRooms(await loadOptions({ building: picked.building, unit_no: picked.unit_no, floor: '' }))
}

async function loadFloorsAfterSkip() {
  applyLevel(await loadOptions({ building: picked.building, unit_no: '' }), 'floor')
}

function showRooms(data) {
  visibility.room = true
  roomOptions.value = data.options || []
}

async function certify() {
  try {
    const result = await unitApi.certify(picked.unitId)
    ElMessage.success(`认证成功，身份：${result.role}`)
  } catch (e) {
    if (e?.response?.data?.code === 'PHONE_NOT_IN_REGISTRY') {
      ElMessage.warning('手机号与清册不一致，可提交产权申诉')
      return
    }
    ElMessage.error(errorText(e))
  }
}

async function uploadProof({ file }) {
  try {
    const uploaded = await attachmentApi.upload(file, 'APPEAL_PROOF')
    appeal.attachmentId = uploaded.id
    ElMessage.success('已上传')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function submitAppeal() {
  try {
    if (!appeal.attachmentId) return ElMessage.warning('请先上传产权证明')
    await unitApi.createAppeal({ unit_id: picked.unitId, proof_ids: [appeal.attachmentId] })
    ElMessage.success('申诉已提交，等待管理员审核')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function applyResident() {
  try {
    await unitApi.createResidentApplication({ unit_id: Number(resident.unitId), note: resident.note })
    ElMessage.success('申请已提交')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function loadToReview() {
  try {
    const data = await unitApi.residentApplicationsToReview()
    toReview.value = data.results || data || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function decideResident(id, action) {
  try {
    await unitApi.decideResidentApplication(id, action)
    ElMessage.success('已处理')
    loadToReview()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

loadBuildings()
</script>
