<!-- MOD-182 / IFC-400：小程序“系统设置”页；界面风格收敛为页内 Tab -->
<template>
  <ThemeRoot>
  <view>
    <view class="settings-tabs">
      <view v-for="t in MP_SETTINGS_TABS" :key="t.key" class="settings-tab is-active">{{ t.label }}</view>
    </view>
    <view id="theme-options" class="card">
      <view class="row">
        <view
          v-for="item in theme.list"
          :key="item.key"
          class="theme-option"
          :class="{ 'is-selected': theme.current === item.key }"
          :data-theme-key="item.key"
          @click="pickTheme(item.key)"
        >
          <view class="theme-swatch"><view v-for="(c, i) in item.swatch" :key="i" :style="{ background: c }" /></view>
          <text class="theme-name">{{ item.name }}</text>
          <text v-if="theme.current === item.key" class="muted">已选</text>
        </view>
      </view>
    </view>
  </view>
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import { useThemeStore } from '@/store/theme'
import { MP_SETTINGS_TABS } from '@/utils/menu'

const theme = useThemeStore()

// 点选即时生效；保存失败回滚并提示（AC-077-04）
async function pickTheme(key) {
  if (key === theme.current) return
  try {
    await theme.select(key)
  } catch (e) {
    uni.showToast({ title: '保存失败', icon: 'none' })
  }
}
</script>

<style scoped>
.settings-tabs { display: flex; gap: 8rpx; margin-bottom: 16rpx; }
.settings-tab {
  flex: 1; padding: 16rpx 8rpx; text-align: center; font-size: 26rpx; border: 1px solid var(--line);
  border-radius: var(--radius-btn); background: var(--surface); color: var(--muted);
}
.settings-tab.is-active { color: var(--accent-text); font-weight: 650; border-color: currentColor; }
</style>
