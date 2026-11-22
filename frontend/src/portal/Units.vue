<!-- MOD-123 / IFC-324 / MOD-176：我的房屋分区宿主；路由 props.section + query.tab 决定显示哪个分区与初始 Tab -->
<template>
  <div class="page">
    <component :is="view" :key="section" :initial-tab="initialTab" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import UnitsIdentity from './units/UnitsIdentity.vue'
import UnitsPick from './units/UnitsPick.vue'
import AppealCenter from './units/AppealCenter.vue'
import UnitsApplications from './units/UnitsApplications.vue'

const props = defineProps({ section: { type: String, default: 'identity' } })
const route = useRoute()

const VIEWS = {
  identity: UnitsIdentity,
  pick: UnitsPick,
  appeal: AppealCenter,
  appeals: AppealCenter,
  applications: UnitsApplications
}
const view = computed(() => VIEWS[props.section] || UnitsIdentity)

// ADR-170：query.tab 只接受分区内白名单，非法值一律回落默认 Tab
const TAB_WHITELIST = {
  identity: ['identity', 'review'],
  appeal: ['appeal', 'mine'],
  appeals: ['mine', 'appeal'],
  applications: ['form', 'records']
}
const TAB_DEFAULTS = { identity: 'identity', appeal: 'appeal', appeals: 'mine', applications: 'form' }

const initialTab = computed(() => {
  const allowed = TAB_WHITELIST[props.section] || []
  const requested = route.query.tab
  if (typeof requested === 'string' && allowed.includes(requested)) return requested
  return TAB_DEFAULTS[props.section] || 'appeal'
})
</script>
