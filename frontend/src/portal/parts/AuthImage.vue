<!-- MOD-082 / IFC-280：带令牌取图（blob URL），卸载与 src 变化时释放
     MOD-155 / REQ-FUNC-256：无头像或加载失败时回退内置默认头像（ADR-149） -->
<template>
  <img v-if="url" :src="url" :alt="alt || '默认头像'" class="auth-image" :style="boxStyle" @error="release" />
  <img v-else :src="avatarDefault" :alt="alt || '默认头像'" class="auth-image" :style="boxStyle" />
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { attachmentApi } from '@/shared/api'
import avatarDefault from '@/assets/avatar-default.svg'

const props = defineProps({
  src: { type: String, default: null },
  alt: { type: String, default: '' },
  size: { type: Number, default: 64 }
})

const url = ref('')
const boxStyle = computed(() => ({ width: `${props.size}px`, height: `${props.size}px` }))

function release() {
  if (url.value) URL.revokeObjectURL(url.value)
  url.value = ''
}

function attachmentId(src) {
  const match = /\/attachments\/([^/]+)\/download/.exec(src || '')
  return match ? match[1] : null
}

async function load() {
  release()
  const id = attachmentId(props.src)
  if (!id) return
  try {
    const blob = await attachmentApi.download(id)
    url.value = URL.createObjectURL(blob)
  } catch (e) {
    url.value = ''
  }
}

watch(() => props.src, load, { immediate: true })
onBeforeUnmount(release)
</script>

<style scoped>
.auth-image {
  border-radius: 50%;
  object-fit: cover;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
}
</style>
