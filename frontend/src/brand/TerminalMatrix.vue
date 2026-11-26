<template>
  <canvas ref="canvasEl" class="auth-matrix" aria-hidden="true" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { startTerminalMatrix } from './terminalMatrix'

const canvasEl = ref(null)
let stop = () => {}

onMounted(() => { stop = startTerminalMatrix(canvasEl.value) })
onBeforeUnmount(() => { stop() })
</script>
