<template>
  <span>{{ prefix }}<span class="brand-at">@</span>{{ suffix }}</span>
</template>

<script setup>
import { BRAND_NAME } from './brand'

const [prefix, suffix] = BRAND_NAME.split('@')
</script>
