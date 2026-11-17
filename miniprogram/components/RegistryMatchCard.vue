<!-- MOD-138 / implements IFC-344：手机号匹配清册后的引导确认卡片（仅 PENDING 时显示；请求不含手机号与姓名） -->
<template>
  <view v-if="matches.length" class="card" id="registry-match">
    <view class="title">发现您名下的专有部分</view>
    <view v-if="matches.length === 1">我们发现您的手机号登记在 {{ matches[0].specific_part }}（{{ matches[0].unit_type_label }}）名下，您是该专有部分的业主吗？</view>
    <view v-else>
      <view>我们发现您的手机号登记在以下 {{ matches.length }} 个专有部分名下，您是这些专有部分的业主吗？可取消勾选不是您的专有部分。</view>
      <view v-for="match in shownMatches" :key="match.unit_id" class="list-item" @click="toggle(match.unit_id)">
        <text>{{ selected.includes(match.unit_id) ? '[已选]' : '[未选]' }} {{ match.specific_part }}（{{ match.unit_type_label }}）</text>
      </view>
      <view v-if="hiddenCount > 0" class="link" @click="expanded = true">展开更多（还有 {{ hiddenCount }} 套）</view>
    </view>
    <view class="muted">已选 {{ selected.length }} 套</view>
    <button class="btn" style="margin-top: 16rpx" :disabled="!selected.length || busy" @click="confirm">是，确认认证</button>
    <button style="margin-top: 16rpx" :disabled="busy" @click="dismiss">不是</button>
  </view>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/utils/api'

const FOLD_LIMIT = 10 // Q-IP-10=A：超过 10 套折叠为"展开更多"，不设硬上限
const emit = defineEmits(['resolved'])
const matches = ref([])
const selected = ref([]) // 默认全选，含折叠部分（Q-IP-17=A）
const expanded = ref(false)
const busy = ref(false)

const shownMatches = computed(() => (expanded.value ? matches.value : matches.value.slice(0, FOLD_LIMIT)))
const hiddenCount = computed(() => (expanded.value ? 0 : Math.max(matches.value.length - FOLD_LIMIT, 0)))

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

function toggle(unitId) {
  selected.value = selected.value.includes(unitId)
    ? selected.value.filter((id) => id !== unitId)
    : [...selected.value, unitId]
}

async function load() {
  try {
    const data = await api.registryMatches()
    matches.value = data?.pending ? data.units || [] : []
    selected.value = matches.value.map((match) => match.unit_id)
  } catch (e) {
    matches.value = []
  }
}

async function confirm() {
  busy.value = true
  try {
    const data = await api.confirmRegistryMatches([...selected.value])
    if (!data.failed) {
      toast(data.succeeded === 1 ? '认证成功，身份：产权业主' : `认证成功，共认证 ${data.succeeded} 套`)
    } else {
      toast(`成功 ${data.succeeded} 套，未成功 ${data.failed} 套`)
    }
    matches.value = []
    emit('resolved')
  } catch (e) {
    toast(e.message)
  } finally {
    busy.value = false
  }
}

async function dismiss() {
  busy.value = true
  try {
    await api.dismissRegistryMatches()
    matches.value = []
    emit('resolved')
  } catch (e) {
    toast(e.message)
  } finally {
    busy.value = false
  }
}

defineExpose({ load })
onMounted(load)
</script>
