<!-- MOD-122：界面风格页（自 Me.vue 原 3-6 行迁移；立即生效、记住选择） -->
<template>
  <div class="page">
    <div class="card">
      <h3 class="title">界面风格</h3>
      <ThemePicker />
    </div>
  </div>
</template>

<script setup>
import ThemePicker from '@/theme/ThemePicker.vue'
</script>
