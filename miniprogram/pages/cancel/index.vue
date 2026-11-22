<!-- MOD-182：账号注销独立页（兼容旧地址 /pages/cancel/index）；内容见 account/panes/CancelPane.vue -->
<template>
  <ThemeRoot>
    <CancelPane />
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import CancelPane from '../account/panes/CancelPane.vue'
</script>
