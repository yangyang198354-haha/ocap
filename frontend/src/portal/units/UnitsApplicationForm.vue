<!-- MOD-171 / IFC-392d：发起同住人申请（房屋 + 本人实名）；重新提交时带入原记录 -->
<template>
  <div>
    <p class="muted">申请成为同住人须填写本人实名；同住人须先有产权业主，由产权业主审批。</p>
    <UnitCascader :key="cascaderKey" v-model="pickedUnitId" />
    <div class="row" style="margin-top: 10px">
      <el-input v-model="applicantName" maxlength="64" placeholder="本人实名" style="width: 220px" />
    </div>
    <div class="row" style="margin-top: 10px">
      <el-button type="primary" :disabled="!pickedUnitId" :loading="submitting" @click="applyResident">
        申请成为同住人
      </el-button>
    </div>
    <p v-if="previousApplicationId" class="muted">重新提交自 #{{ previousApplicationId }}</p>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { errorText } from '@/shared/format'
import { unitApi } from '@/shared/api'
import { useHousingStore } from '@/stores/housing'
import UnitCascader from '../parts/UnitCascader.vue'

const props = defineProps({ prefill: { type: Object, default: null } })
const emit = defineEmits(['submitted'])

const NAME_MAX = 64
const store = useHousingStore()
const pickedUnitId = ref(null)
const applicantName = ref('')
const previousApplicationId = ref(null)
const cascaderKey = ref(0)
const submitting = ref(false)

function applyPrefill(value) {
  if (!value || !value.nonce) return
  pickedUnitId.value = value.unitId || null
  applicantName.value = value.applicantName || ''
  previousApplicationId.value = value.previousApplicationId || null
  cascaderKey.value += 1
}

watch(() => props.prefill, applyPrefill, { deep: true })

async function applyResident() {
  const name = applicantName.value.trim()
  if (!name) return ElMessage.warning('请输入本人实名')
  if (name.length > NAME_MAX) return ElMessage.warning(`实名不超过 ${NAME_MAX} 字`)
  submitting.value = true
  try {
    await unitApi.createResidentApplication({
      unit_id: pickedUnitId.value,
      applicant_name: name,
      ...(previousApplicationId.value ? { previous_application_id: previousApplicationId.value } : {})
    })
    ElMessage.success('申请已提交，等待产权业主审批')
    pickedUnitId.value = null
    applicantName.value = ''
    previousApplicationId.value = null
    cascaderKey.value += 1
    await store.loadLists()
    emit('submitted')
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    submitting.value = false
  }
}

onMounted(() => applyPrefill(props.prefill))
</script>
