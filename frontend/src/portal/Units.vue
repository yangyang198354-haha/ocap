<!-- MOD-123 / IFC-324：我的房屋分区宿主；路由 props.section 决定显示哪个分区（逻辑见 portal/units/*） -->
<template>
  <div class="page">
    <component :is="view" :key="section" :initial-tab="initialTab" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import UnitsIdentity from './units/UnitsIdentity.vue'
import UnitsPick from './units/UnitsPick.vue'
import AppealCenter from './units/AppealCenter.vue'
import UnitsApplications from './units/UnitsApplications.vue'

const props = defineProps({ section: { type: String, default: 'identity' } })

const VIEWS = {
  identity: UnitsIdentity,
  pick: UnitsPick,
  appeal: AppealCenter,
  appeals: AppealCenter,
  applications: UnitsApplications
}
const view = computed(() => VIEWS[props.section] || UnitsIdentity)
const initialTab = computed(() => {
  if (props.section === 'appeals') return 'mine'
  if (props.section === 'applications') return 'form'
  return 'appeal'
})
</script>
