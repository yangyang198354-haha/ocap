<template>
  <img class="brand-mark" :src="markSrc" :width="size" :height="size" alt="" aria-hidden="true" draggable="false" />
</template>

<script setup>
import markSrc from './assets/maple-leaf.png'

defineProps({ size: { type: Number, default: 32 } })
</script>
