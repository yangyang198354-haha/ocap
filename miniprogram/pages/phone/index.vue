<!-- MOD-182：绑定手机独立页（兼容旧地址 /pages/phone/index）；内容见 account/panes/PhonePane.vue -->
<template>
  <ThemeRoot>
    <PhonePane />
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import PhonePane from '../account/panes/PhonePane.vue'
</script>
