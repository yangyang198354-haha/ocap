<!-- MOD-182 / IFC-401：小程序“个人资料”页；绑定手机/邮箱验证/账号注销收敛为页内 Tab，不再直接出现在“我的”列表 -->
<template>
  <ThemeRoot>
  <view>
    <view class="account-tabs">
      <view
        v-for="t in MP_ACCOUNT_TABS"
        :key="t.key"
        class="account-tab"
        :class="{ 'is-active': tab === t.key }"
        @click="tab = t.key"
      >
        {{ t.label }}
      </view>
    </view>
    <ProfilePane v-if="tab === 'profile'" />
    <PhonePane v-else-if="tab === 'phone'" />
    <EmailPane v-else-if="tab === 'email'" />
    <CancelPane v-else />
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import ProfilePane from './panes/ProfilePane.vue'
import PhonePane from './panes/PhonePane.vue'
import EmailPane from './panes/EmailPane.vue'
import CancelPane from './panes/CancelPane.vue'
import { ref } from 'vue'
import { MP_ACCOUNT_TABS } from '@/utils/menu'

const tab = ref('profile')
</script>

<style scoped>
.account-tabs { display: flex; gap: 8rpx; margin-bottom: 16rpx; }
.account-tab {
  flex: 1; padding: 16rpx 8rpx; text-align: center; font-size: 26rpx; border: 1px solid var(--line);
  border-radius: var(--radius-btn); background: var(--surface); color: var(--muted);
}
.account-tab.is-active { color: var(--accent-text); font-weight: 650; border-color: currentColor; }
</style>
