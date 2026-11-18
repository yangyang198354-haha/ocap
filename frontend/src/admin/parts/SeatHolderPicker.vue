<!-- MOD-152 / IFC-364、IFC-350：逐级选专有部分（管理端选项接口），再从该专有部分的清册业主中选一位；手机号已脱敏，不出现 ID 输入框 -->
<template>
  <div class="seat-holder-picker">
    <UnitCascader v-model="unitId" :fetcher="admin.unitOptions" />
    <p v-if="unitId && !candidates.length && loaded" class="muted">该专有部分暂无可选的清册业主</p>
    <el-radio-group v-if="candidates.length" :model-value="modelValue" class="seat-holder-owners" @update:model-value="pick">
      <el-radio v-for="o in candidates" :key="o.owner_id" :value="o.owner_id" :disabled="o.seated">
        {{ o.name }}
        <span class="muted">{{ o.phone_masked || '无手机号' }}</span>
        <el-tag v-if="o.registered" size="small" type="info">已注册</el-tag>
        <el-tag v-if="o.seated" size="small" type="warning">已有有效席位</el-tag>
      </el-radio>
    </el-radio-group>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'
import UnitCascader from '@/portal/parts/UnitCascader.vue'

// modelValue：被选清册业主 id（registry_owner_id）
defineProps({ modelValue: { type: Number, default: null } })
const emit = defineEmits(['update:modelValue'])

const unitId = ref(null)
const candidates = ref([])
const loaded = ref(false)

function pick(value) {
  emit('update:modelValue', value)
}

watch(unitId, async (id) => {
  candidates.value = []
  loaded.value = false
  emit('update:modelValue', null)
  if (!id) return
  try {
    const data = await admin.ownerCandidates({ unit_id: id })
    candidates.value = data?.owners || []
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    loaded.value = true
  }
})
</script>

<style scoped>
.seat-holder-owners { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; margin-top: 10px; }
</style>
