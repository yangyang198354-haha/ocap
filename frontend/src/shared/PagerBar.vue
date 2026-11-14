<!-- MOD-082 辅助：总条数 + 翻页控件（总数不超过每页条数时不显示翻页控件） -->
<template>
  <div class="pager-bar">
    <span class="muted pager-total">共 {{ total }} 条</span>
    <el-pagination
      v-if="total > pageSize"
      background
      layout="prev, pager, next"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="(n) => emit('change', n)"
    />
  </div>
</template>

<script setup>
defineProps({
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 }
})
const emit = defineEmits(['change'])
</script>

<style scoped>
.pager-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}
</style>
