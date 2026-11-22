<!-- MOD-182：邮箱验证独立页（兼容旧地址 /pages/email/index）；内容见 account/panes/EmailPane.vue -->
<template>
  <ThemeRoot>
    <EmailPane @verified="goBack" />
  </ThemeRoot>
</template>

<script setup>
import ThemeRoot from '@/components/ThemeRoot.vue'
import EmailPane from '../account/panes/EmailPane.vue'

function goBack() {
  uni.navigateBack()
}
</script>
