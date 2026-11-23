<!-- MOD-084 / IFC-280：按姓名（清册实名）/ 手机号后四位 / 账号搜索并选择注册用户，不出现用户 ID 输入框 -->
<template>
  <div class="user-picker">
    <el-input
      v-model="keyword"
      :placeholder="placeholder"
      maxlength="32"
      clearable
      @input="onInput"
      @clear="reset"
    />
    <div v-if="selected" class="user-picker-selected">
      <AuthImage :src="selected.avatar_url" :alt="displayNameOf(selected)" :size="24" />
      已选：<b>{{ displayNameOf(selected) }}</b>
      <el-tag size="small" type="info">{{ selected.identity_label }}</el-tag>
      <el-button size="small" link @click="clear">重新选择</el-button>
    </div>
    <div v-if="searched" class="user-picker-list">
      <p v-if="!candidates.length" class="muted">无匹配用户</p>
      <div v-for="c in candidates" :key="c.id" class="user-picker-item" @click="choose(c)">
        <AuthImage :src="c.avatar_url" :alt="displayNameOf(c)" :size="24" />
        <b>{{ displayNameOf(c) }}</b>
        <span class="muted">{{ c.account_no }}</span>
        <span class="muted">{{ c.phone || '未绑定手机' }}</span>
        <el-tag size="small" type="info">{{ c.identity_label }}</el-tag>
      </div>
      <el-pagination
        v-if="total > PAGE_SIZE"
        small
        layout="prev, pager, next"
        :total="total"
        :page-size="PAGE_SIZE"
        :current-page="page"
        @current-change="goto"
      />
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { admin } from '@/shared/api'
import { errorText } from '@/shared/format'
import AuthImage from '@/portal/parts/AuthImage.vue'

const displayNameOf = (u) => u.real_names?.[0] || u.display_name || u.account_no || `用户#${u.id}`

defineProps({
  modelValue: { type: Number, default: null },
  placeholder: { type: String, default: '输入姓名、手机号后四位或账号搜索用户' }
})
const emit = defineEmits(['update:modelValue', 'change'])

const PAGE_SIZE = 10
const keyword = ref('')
const candidates = ref([])
const total = ref(0)
const page = ref(1)
const searched = ref(false)
const selected = ref(null)
let timer = null

async function search() {
  const q = keyword.value.trim().slice(0, 32)
  if (!q) {
    reset()
    return
  }
  try {
    const data = await admin.users({ q, page: page.value, page_size: PAGE_SIZE })
    candidates.value = data.results || data || []
    total.value = data.count ?? candidates.value.length
    searched.value = true
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function onInput() {
  clearTimeout(timer)
  page.value = 1
  timer = setTimeout(search, 300)
}

function goto(n) {
  page.value = n
  return search()
}

function reset() {
  clearTimeout(timer)
  candidates.value = []
  total.value = 0
  searched.value = false
}

function choose(c) {
  selected.value = c
  reset()
  keyword.value = ''
  emit('update:modelValue', c.id)
  emit('change', c)
}

function clear() {
  selected.value = null
  emit('update:modelValue', null)
  emit('change', null)
}

onBeforeUnmount(() => clearTimeout(timer))
</script>

<style scoped>
.user-picker-item {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  padding: 6px 4px;
  cursor: pointer;
}
.user-picker-selected {
  margin-top: 6px;
  display: flex;
  gap: 8px;
  align-items: center;
}
</style>
