<!-- MOD-122 / MOD-178：系统设置页（自 Me.vue 原 3-6 行迁移；立即生效、记住选择）
     界面风格收敛为本页 Tab，不再直接出现在右上角下拉菜单 -->
<template>
  <div class="page">
    <PageHead title="系统设置" />
    <div class="card">
      <el-tabs v-model="activeTab" class="me-settings-tabs">
        <el-tab-pane label="界面风格" name="style">
          <ThemePicker />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import PageHead from '@/shared/PageHead.vue'
import { ref } from 'vue'
import ThemePicker from '@/theme/ThemePicker.vue'

defineProps({ initialTab: { type: String, default: 'style' } })

const activeTab = ref('style')
</script>
