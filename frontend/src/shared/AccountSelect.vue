<!-- MOD-204 / IFC-420：仅启用账户的选择器，自动加载并默认选中默认账户 -->
<template>
  <el-select
    :model-value="modelValue"
    :disabled="disabled"
    :size="size"
    :placeholder="placeholder"
    class="account-select"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <el-option
      v-for="account in accounts"
      :key="account.id"
      :label="account.is_default ? `${account.name}（默认）` : account.name"
      :value="account.id"
    />
    <template #empty>
      <div class="account-select-empty muted">暂无可用账户</div>
    </template>
  </el-select>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { accountApi } from '@/shared/api'

const props = defineProps({
  modelValue: { type: Number, default: null },
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: '请选择入账账户' },
  size: { type: String, default: 'default' }
})
const emit = defineEmits(['update:modelValue', 'loaded'])
const accounts = ref([])

onMounted(async () => {
  try {
    const data = await accountApi.summary({ status: 'ENABLED', recent: 0 })
    accounts.value = data?.accounts || []
  } catch (e) {
    accounts.value = []
  }
  const defaultAccount = accounts.value.find((a) => a.is_default) || accounts.value[0] || null
  if (props.modelValue === null && defaultAccount) emit('update:modelValue', defaultAccount.id)
  emit('loaded', { accounts: accounts.value, defaultId: defaultAccount ? defaultAccount.id : null })
})
</script>

<style scoped>
.account-select { width: 100%; }
.account-select-empty { padding: 8px 12px; font-size: 13px; }
</style>
