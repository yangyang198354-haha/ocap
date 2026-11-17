<!-- MOD-123 / IFC-324：我的房屋分区宿主；路由 props.section 决定显示哪个分区（逻辑见 portal/units/*） -->
<template>
  <div class="page">
    <component :is="view" :key="section" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import UnitsIdentity from './units/UnitsIdentity.vue'
import UnitsPick from './units/UnitsPick.vue'
import UnitsAppeal from './units/UnitsAppeal.vue'
import UnitsApplications from './units/UnitsApplications.vue'
import UnitsMyAppeals from './units/UnitsMyAppeals.vue'

const props = defineProps({ section: { type: String, default: 'identity' } })

const VIEWS = {
  identity: UnitsIdentity,
  pick: UnitsPick,
  appeal: UnitsAppeal,
  applications: UnitsApplications,
  appeals: UnitsMyAppeals
}
const view = computed(() => VIEWS[props.section] || UnitsIdentity)
</script>
