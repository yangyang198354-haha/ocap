<!-- MOD-082 辅助：总条数 + 每页条数（可选）+ 翻页控件（总数不超过每页条数时不显示翻页控件） -->
<template>
  <div class="pager-bar">
    <span class="muted pager-total">共 {{ total }} 条</span>
    <el-select
      v-if="sizable"
      class="pager-size"
      :model-value="pageSize"
      size="small"
      aria-label="每页条数"
      @change="changeSize"
    >
      <el-option v-for="n in sizes" :key="n" :label="`${n} 条/页`" :value="n" />
    </el-select>
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
  pageSize: { type: Number, default: 20 },
  // REQ-FUNC-283：四个管理列表启用每页条数选择，其余列表保持原样
  sizable: { type: Boolean, default: false }
})
const emit = defineEmits(['change', 'update:pageSize'])
const sizes = [20, 50, 100]

function changeSize(n) {
  emit('update:pageSize', n)
}
</script>

<style scoped>
.pager-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}
.pager-size {
  width: 110px;
}
</style>
