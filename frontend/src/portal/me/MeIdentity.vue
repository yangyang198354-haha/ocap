<!-- MOD-122：我的身份页（自 Me.vue 原 8-16、147-153 行迁移） -->
<template>
  <div class="page">
    <div class="card">
      <h3 class="title">身份</h3>
      <p>汇总身份：<el-tag>{{ auth.identitySummary.label }}</el-tag></p>
      <p v-if="!housing.units.length" class="muted">暂无已认证房屋</p>
      <p v-for="unit in housing.units" :key="unit.unit_id" class="row">
        <span>{{ unit.specific_part }}</span>
        <el-tag size="small" type="info">{{ unit.role_label }}</el-tag>
      </p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { meApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const housing = reactive({ units: [] })

async function loadHousing() {
  try {
    Object.assign(housing, await meApi.housing())
  } catch (e) {
    housing.units = []
  }
}

onMounted(loadHousing)
</script>
