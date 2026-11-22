<!-- MOD-179 / IFC-398：小程序“我的房屋”三 Tab 宿主（身份与房屋 / 我的认证与申述 / 我的同住人申请，ADR-169） -->
<template>
  <ThemeRoot>
  <view>
    <RegistryMatchCard ref="matchCard" @resolved="onMatchResolved" />
    <view class="housing-tabs">
      <view
        v-for="t in MP_HOUSING_TABS"
        :key="t.key"
        class="housing-tab"
        :class="{ 'is-active': tab === t.key }"
        @click="tab = t.key"
      >
        {{ t.label }}
      </view>
    </view>
    <IdentityPane
      v-show="tab === 'identity'"
      :housing="housing"
      :owns-any-unit="ownsAnyUnit"
      :initial-review="reviewRequested"
      @refresh="loadHousing"
      @appeal="onAppealRequested"
    />
    <AppealPane v-show="tab === 'appeal'" :prefill-name="appealPrefillName" />
    <ResidentPane v-show="tab === 'applications'" @refresh="loadHousing" />
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import RegistryMatchCard from '@/components/RegistryMatchCard.vue'
import IdentityPane from './components/IdentityPane.vue'
import AppealPane from './components/AppealPane.vue'
import ResidentPane from './components/ResidentPane.vue'
import { computed, reactive, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { api } from '@/utils/api'
import { MP_HOUSING_TABS } from '@/utils/menu'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const tab = ref('identity')
const reviewRequested = ref(false)
const appealPrefillName = ref('')
const housing = reactive({ summary: { code: 'GUEST', label: '游客' }, units: [], pending_review_count: 0 })

const isOwner = (unit) => unit.role === 'HEAD' || unit.role === 'OWNER'
// 仅产权业主显示“待我审批”子 Tab（仅展示控制；权限由后端 403 把关）
const ownsAnyUnit = computed(() => housing.units.some((unit) => isOwner(unit)))

async function onMatchResolved() {
  await auth.fetchMe().catch(() => null)
  await loadHousing()
}

function toast(title) {
  uni.showToast({ title, icon: 'none' })
}

async function loadHousing() {
  try {
    Object.assign(housing, await api.housing())
  } catch (e) {
    toast(e.message)
  }
}

function onAppealRequested(name) {
  appealPrefillName.value = typeof name === 'string' ? name : ''
  tab.value = 'appeal'
}

onLoad((query) => {
  const flag = String(query?.review ?? '')
  if (flag === '1' || flag === 'true') {
    tab.value = 'identity'
    reviewRequested.value = true
  }
})

onShow(loadHousing)
</script>

<style scoped>
.housing-tabs { display: flex; gap: 8rpx; margin-bottom: 16rpx; }
.housing-tab {
  flex: 1; text-align: center; padding: 18rpx 0; font-size: 26rpx; color: var(--muted);
  background: var(--surface); border: 1px solid var(--line); border-radius: var(--radius-md);
}
.housing-tab.is-active { color: var(--accent-text); font-weight: 650; border-color: currentColor; }
</style>
