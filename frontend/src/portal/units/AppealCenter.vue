<!-- MOD-170 / IFC-392a：申诉中心宿主；双 Tab 承载“认证申诉”与“我的申诉”，切换不销毁子组件 -->
<template>
  <div class="card">
    <el-tabs v-model="tab">
      <el-tab-pane label="认证申诉" name="appeal">
        <UnitsAppeal ref="appealRef" :prefill="prefill" @submitted="onSubmitted" />
      </el-tab-pane>
      <el-tab-pane label="我的申诉" name="mine">
        <UnitsMyAppeals @resubmit="onResubmit" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import UnitsAppeal from './UnitsAppeal.vue'
import UnitsMyAppeals from './UnitsMyAppeals.vue'

const props = defineProps({ initialTab: { type: String, default: 'appeal' } })
const tab = ref(props.initialTab === 'mine' ? 'mine' : 'appeal')
const appealRef = ref(null)
const prefill = reactive({ unitId: null, ownerName: '', previousAppealId: null, nonce: 0 })

function onSubmitted() {
  tab.value = 'mine'
}

function onResubmit(row) {
  prefill.unitId = row.unit?.unit_id || null
  prefill.ownerName = row.owner_name || ''
  prefill.previousAppealId = row.id
  prefill.nonce += 1
  tab.value = 'appeal'
}
</script>
