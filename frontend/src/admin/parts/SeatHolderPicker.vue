<!-- MOD-152 / IFC-364、IFC-350：逐级选专有部分，或按姓名/手机号搜索清册业主；不出现 ID 输入框 -->
<template>
  <div class="seat-holder-picker">
    <UnitCascader v-model="unitId" :fetcher="admin.unitOptions" />
    <p v-if="unitId && !candidates.length && loaded" class="muted">该专有部分暂无可选的清册业主</p>
    <el-radio-group v-if="candidates.length" :model-value="modelValue" class="seat-holder-owners" @update:model-value="pick">
      <el-radio v-for="o in candidates" :key="o.owner_id" :value="o.owner_id" :disabled="o.seated">
        {{ o.name }}
        <span class="muted">{{ o.phone || '无手机号' }}</span>
        <el-tag v-if="o.registered" size="small" type="info">已注册</el-tag>
        <el-tag v-if="o.seated" size="small" type="warning">已有有效席位</el-tag>
      </el-radio>
    </el-radio-group>

    <p class="seat-holder-divider">或按姓名 / 手机号搜索</p>
    <div class="seat-holder-search">
      <el-input v-model="keyword" clearable placeholder="姓名或手机号（至少 2 个字符）" @keyup.enter="search" />
      <el-button :loading="searching" @click="search">搜索</el-button>
    </div>
    <p v-if="searchError" class="error-text">{{ searchError }}</p>
    <p v-else-if="searched && !results.length" class="muted">未找到匹配的清册业主</p>
    <el-radio-group v-if="results.length" :model-value="modelValue" class="seat-holder-owners" @update:model-value="pick">
      <el-radio v-for="o in results" :key="`search-${o.owner_id}`" :value="o.owner_id" :disabled="o.seated">
        {{ o.name }}
        <span class="muted">{{ o.phone || '无手机号' }}</span>
        <span class="muted">{{ o.unit_text }}</span>
        <el-tag v-if="o.registered" size="small" type="info">已注册</el-tag>
        <el-tag v-if="o.seated" size="small" type="warning">已有有效席位</el-tag>
      </el-radio>
    </el-radio-group>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
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
const keyword = ref('')
const results = ref([])
const searched = ref(false)
const searching = ref(false)
const searchError = ref('')
let searchTimer = null

function pick(value) {
  emit('update:modelValue', value)
}

async function search() {
  clearTimeout(searchTimer)
  const kw = keyword.value.trim()
  if (kw.length < 2) {
    ElMessage.warning('请输入至少 2 个字符的姓名或手机号')
    return
  }
  searching.value = true
  searchError.value = ''
  try {
    const data = await admin.ownerSearch({ keyword: kw })
    results.value = data?.owners || []
    searched.value = true
  } catch (e) {
    results.value = []
    searched.value = false
    searchError.value = errorText(e)
  } finally {
    searching.value = false
  }
}

// 输入停顿 300ms 自动搜索，回车或“搜索”按钮立即检索
watch(keyword, (value) => {
  clearTimeout(searchTimer)
  const kw = (value || '').trim()
  if (kw.length < 2) {
    results.value = []
    searched.value = false
    searchError.value = ''
    return
  }
  searchTimer = setTimeout(search, 300)
})

onBeforeUnmount(() => clearTimeout(searchTimer))

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
.seat-holder-divider { margin: 14px 0 8px; padding-top: 10px; border-top: 1px dashed var(--el-border-color-lighter); color: var(--muted); font-size: 13px; }
.seat-holder-search { display: flex; gap: 8px; }
.seat-holder-search .el-input { flex: 1; }
</style>
