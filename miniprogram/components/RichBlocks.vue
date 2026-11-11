<template>
  <view class="rich-blocks">
    <template v-for="(block, index) in blocks" :key="index">
      <view v-if="block.type === 'paragraph' || block.type === 'heading'" :style="blockStyle(block)">
        <text v-for="(inline, i) in block.inlines || []" :key="i" :style="inlineStyle(inline, block)"
              @tap="openLink(inline)" @click="openLink(inline)">{{ inline.text }}</text>
      </view>
      <view v-else-if="block.type === 'bullet_list' || block.type === 'ordered_list'">
        <view v-for="(item, n) in block.items || []" :key="n" class="list-item">
          <text>{{ block.type === 'ordered_list' ? `${(block.start || 1) + n}. ` : '• ' }}</text>
          <rich-blocks :blocks="item" :theme="theme" :api-base="apiBase" />
        </view>
      </view>
      <view v-else-if="block.type === 'quote'" class="quote">
        <rich-blocks :blocks="block.children || []" :theme="theme" :api-base="apiBase" />
      </view>
      <view v-else-if="block.type === 'hr'" class="hr" />
      <image v-else-if="block.type === 'image'" :src="mediaUrl(block.src)" mode="widthFix" @tap="preview(block.src)" />
      <video v-else-if="block.type === 'video'" :src="mediaUrl(block.src)" controls />
      <view v-else-if="block.type === 'page_break'" class="page-break" />
    </template>
  </view>
</template>

<script setup>
import { mediaUrl } from '@/utils/http'

defineProps({
  blocks: { type: Array, default: () => [] },
  theme: { type: Object, default: () => ({}) },
  apiBase: { type: String, default: '' }
})

function blockStyle(block) {
  const style = {}
  if (block.align) style.textAlign = block.align
  if (block.type === 'heading') style.fontWeight = '700'
  else style.marginBottom = '12rpx'
  return style
}
function inlineStyle(inline, block) {
  const style = {}
  if (inline.bold) style.fontWeight = '700'
  if (inline.italic) style.fontStyle = 'italic'
  if (inline.underline || inline.href) style.textDecoration = 'underline'
  if (inline.strike) style.textDecoration = 'line-through'
  if (inline.color) style.color = inline.color
  if (inline.bg) style.backgroundColor = inline.bg
  if (inline.size) style.fontSize = `${inline.size}px`
  if (inline.lh) style.lineHeight = inline.lh
  if (block.level) style.fontSize = `${26 - block.level * 2}px`
  return style
}
function openLink(inline) {
  if (!inline.href) return
  uni.setClipboardData({
    data: inline.href,
    success: () => uni.showToast({ title: '链接已复制，请在浏览器中打开', icon: 'none' })
  })
}
function preview(src) {
  uni.previewImage({ urls: [mediaUrl(src)] })
}
defineExpose({ openLink })
</script>

<style scoped>
.rich-blocks { font-size: 30rpx; line-height: 1.8; }
.list-item { display: flex; }
.quote { border-left: 6rpx solid var(--line); padding-left: 16rpx; color: var(--muted); }
.hr { height: 2rpx; background: var(--line); margin: 24rpx 0; }
.page-break { height: 2rpx; border-top: 2rpx dashed var(--line); margin: 24rpx 0; }
image, video { width: 100%; margin: 16rpx 0; }
</style>
