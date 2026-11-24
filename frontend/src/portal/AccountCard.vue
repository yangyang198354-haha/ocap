<template>
  <article
    class="card account-card"
    :class="{ 'is-selected': selected }"
    role="button"
    tabindex="0"
    :aria-pressed="selected ? 'true' : 'false'"
    @click="emit('select', account.id)"
    @keydown.enter.prevent="emit('select', account.id)"
    @keydown.space.prevent="emit('select', account.id)"
  >
    <header class="account-card-head">
      <div class="account-card-title">
        <b>{{ account.name }}</b>
        <span v-if="account.is_default" class="chip">默认账户</span>
        <span v-if="account.status === 'DISABLED'" class="tag is-warning">已停用</span>
      </div>
      <div v-if="account.account_no" class="label mono">账号 {{ account.account_no }}</div>
    </header>
    <div class="account-balance mono">¥{{ moneyText(account.balance) }}</div>
    <div v-if="!entries.length" class="muted account-empty">暂无收支记录</div>
    <ul v-else class="account-entries">
      <li v-for="entry in entries" :key="entry.id" class="account-entry">
        <span class="account-entry-date mono">{{ entry.occurred_on }}</span>
        <span class="account-entry-dir" :class="entry.direction === 'INCOME' ? 'is-income' : 'is-expense'">
          {{ entry.direction === 'INCOME' ? '收入' : '支出' }}
        </span>
        <span class="account-entry-type">{{ entryTypeText(entry.entry_type) }}</span>
        <span class="account-entry-amount mono">¥{{ moneyText(entry.amount) }}</span>
      </li>
    </ul>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { moneyText } from '@/shared/format'

const props = defineProps({
  account: { type: Object, required: true },
  selected: { type: Boolean, default: false }
})
const emit = defineEmits(['select'])
const entries = computed(() => props.account.recent_entries || [])
const ENTRY_TYPES = { REIMBURSEMENT: '报销', ADVANCE: '备用金', SETTLEMENT: '核销', INCOME: '收入' }
const entryTypeText = (t) => ENTRY_TYPES[t] || t || '收支'
</script>

<style scoped>
.account-card { margin-bottom: 0; display: flex; flex-direction: column; gap: 8px; cursor: pointer; transition: border-color .15s ease, box-shadow .15s ease; }
.account-card:focus-visible { outline: 2px solid var(--accent-text); outline-offset: 2px; }
.account-card.is-selected { border-color: var(--accent-text); box-shadow: 0 0 0 1px var(--accent-text) inset; }
.account-card-head { display: flex; flex-direction: column; gap: 4px; }
.account-card-title { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.account-card-title b { font-size: 15px; }
.account-balance { font-size: 28px; font-weight: 700; letter-spacing: -0.01em; line-height: 1.2; }
.account-empty { margin: 4px 0 0; }
.account-entries { list-style: none; margin: 4px 0 0; padding: 0; }
.account-entry {
  display: grid; grid-template-columns: 88px 40px minmax(0, 1fr) auto;
  gap: 8px; align-items: center; padding: 6px 0; font-size: 12px;
  border-top: 1px solid var(--line);
}
.account-entry-date { color: var(--muted); }
.account-entry-dir { font-size: 12px; }
.account-entry-dir.is-income { color: var(--success); }
.account-entry-dir.is-expense { color: var(--danger); }
.account-entry-type { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.account-entry-amount { text-align: right; }
@media (min-width: 768px) {
  .account-balance { font-size: 32px; }
}
</style>
