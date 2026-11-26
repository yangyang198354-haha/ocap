<!-- MOD-137 / implements IFC-342：手机号匹配清册后的引导确认面板（仅 PENDING 时显示；请求不含手机号与姓名） -->
<template>
  <div v-if="matches.length" class="card registry-match" id="registry-match">
    <h2 class="title">发现您名下的专有部分</h2>
    <p v-if="matches.length === 1">
      我们发现您的手机号登记在 {{ matches[0].specific_part }}（{{ matches[0].unit_type_label }}）名下，您是该专有部分的业主吗？
    </p>
    <template v-else>
      <p>我们发现您的手机号登记在以下 {{ matches.length }} 个专有部分名下，您是这些专有部分的业主吗？可取消勾选不是您的专有部分。</p>
      <div v-for="match in shownMatches" :key="match.unit_id" class="row">
        <el-checkbox :model-value="selected.has(match.unit_id)" @change="toggle(match.unit_id)">
          {{ match.specific_part }}（{{ match.unit_type_label }}）
        </el-checkbox>
      </div>
      <el-button v-if="hiddenCount > 0" link type="primary" @click="expanded = true">展开更多（还有 {{ hiddenCount }} 套）</el-button>
    </template>
    <div class="row" style="margin-top: 10px">
      <el-button type="primary" :disabled="!selected.size || busy" @click="confirm">是，确认认证</el-button>
      <span class="muted">已选 {{ selected.size }} 套</span>
      <el-button :disabled="busy" @click="dismiss">不是</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { meApi } from '@/shared/api'
import { errorText } from '@/shared/format'
import { useAuthStore } from '@/stores/auth'
import { useHousingStore } from '@/stores/housing'

const FOLD_LIMIT = 10 // Q-IP-10=A：超过 10 套折叠为"展开更多"，不设硬上限

const emit = defineEmits(['resolved'])
const auth = useAuthStore()
const store = useHousingStore()
const matches = ref([])
const selected = ref(new Set()) // 默认全选，含折叠部分（Q-IP-17=A）
const expanded = ref(false)
const busy = ref(false)

const shownMatches = computed(() => (expanded.value ? matches.value : matches.value.slice(0, FOLD_LIMIT)))
const hiddenCount = computed(() => (expanded.value ? 0 : Math.max(matches.value.length - FOLD_LIMIT, 0)))

function toggle(unitId) {
  const next = new Set(selected.value)
  if (next.has(unitId)) next.delete(unitId)
  else next.add(unitId)
  selected.value = next
}

async function load() {
  try {
    const data = await meApi.registryMatches()
    matches.value = data?.pending ? data.units || [] : []
    selected.value = new Set(matches.value.map((match) => match.unit_id))
  } catch (e) {
    matches.value = []
  }
}

async function confirm() {
  busy.value = true
  try {
    const data = await meApi.confirmRegistryMatches([...selected.value])
    if (!data.failed) {
      ElMessage.success(data.succeeded === 1 ? '认证成功，身份：产权业主' : `认证成功，共认证 ${data.succeeded} 套`)
    } else {
      ElMessage.warning(`成功 ${data.succeeded} 套，未成功 ${data.failed} 套`)
    }
    matches.value = []
    await auth.fetchMe().catch(() => null)
    await store.refresh().catch(() => null)
    emit('resolved')
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    busy.value = false
  }
}

async function dismiss() {
  busy.value = true
  try {
    await meApi.dismissRegistryMatches()
    matches.value = []
    emit('resolved')
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    busy.value = false
  }
}

onMounted(load)
</script>
