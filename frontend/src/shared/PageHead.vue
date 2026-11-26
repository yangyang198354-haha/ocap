<!-- MOD-220 / IFC-453：页面标题区，保证每个页面只有一个 h1；decor 由 .page-head 提供 -->
<template>
  <header class="page-head">
    <div class="page-head-main">
      <h1 class="page-title" :class="{ 'sr-only': srOnly }">{{ title }}</h1>
      <p v-if="description" class="page-desc">{{ description }}</p>
    </div>
    <div v-if="$slots.default" class="page-actions"><slot /></div>
  </header>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: '' },
  srOnly: { type: Boolean, default: false }
})
</script>
