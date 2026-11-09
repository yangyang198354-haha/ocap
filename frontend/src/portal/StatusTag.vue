<template>
  <span class="tag" :class="`is-${tone}`"><i class="tag-dot" aria-hidden="true" />{{ text }}</span>
</template>

<script setup>
import { computed } from 'vue'

// 状态标签：圆点 + 文字 + 底色（REQ-FUNC-082）；未知状态显示原值，不靠颜色单独表达
const props = defineProps({ status: { type: String, default: '' } })

const MAP = {
  PENDING: ['审批中', 'warning'],
  OPEN: ['进行中', 'warning'],
  DRAFT: ['草稿', 'neutral'],
  APPROVED: ['通过', 'success'],
  EFFECTIVE: ['已生效', 'success'],
  REJECTED: ['未通过', 'danger'],
  WITHDRAWN: ['已撤回', 'danger'],
  CLOSED: ['已截止', 'neutral']
}
const text = computed(() => MAP[props.status]?.[0] || props.status)
const tone = computed(() => MAP[props.status]?.[1] || 'neutral')
</script>
