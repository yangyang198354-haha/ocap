<!-- MOD-171 / IFC-392c：同住申请中心宿主；双 Tab 承载“发起申请”与“申请记录” -->
<template>
  <div class="card">
    <h3 class="title">我的同住人申请</h3>
    <el-tabs v-model="tab">
      <el-tab-pane label="发起申请" name="form">
        <UnitsApplicationForm :prefill="prefill" @submitted="onSubmitted" />
      </el-tab-pane>
      <el-tab-pane label="申请记录" name="records">
        <UnitsApplicationRecords @resubmit="onResubmit" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import UnitsApplicationForm from './UnitsApplicationForm.vue'
import UnitsApplicationRecords from './UnitsApplicationRecords.vue'

const props = defineProps({ initialTab: { type: String, default: 'form' } })
const tab = ref(props.initialTab === 'records' ? 'records' : 'form')
const prefill = reactive({ unitId: null, applicantName: '', previousApplicationId: null, nonce: 0 })

function onSubmitted() {
  tab.value = 'records'
}

function onResubmit(row) {
  prefill.unitId = row.unit?.unit_id || null
  prefill.applicantName = row.applicant_name || ''
  prefill.previousApplicationId = row.id
  prefill.nonce += 1
  tab.value = 'form'
}
</script>
