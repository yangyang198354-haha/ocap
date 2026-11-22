<template>
  <div class="steps-editor">
    <div v-for="(step, index) in steps" :key="index" class="card" style="margin-top: 8px">
      <div class="row" style="justify-content: space-between">
        <b>第 {{ index + 1 }} 步</b>
        <span>
          <el-button size="small" link :disabled="index === 0" @click="$emit('move', index, -1)">上移</el-button>
          <el-button size="small" link :disabled="index === steps.length - 1" @click="$emit('move', index, 1)">下移</el-button>
          <el-button size="small" link type="danger" @click="$emit('remove', index)">删除</el-button>
        </span>
      </div>
      <el-input v-model="step.name" maxlength="60" placeholder="步骤名称（如：财务初审）" style="margin-top: 6px" />
      <el-radio-group v-model="step.strategy" style="margin-top: 6px">
        <el-radio label="ANY">或签（任一通过）</el-radio>
        <el-radio label="ALL">会签（全部同意）</el-radio>
      </el-radio-group>
      <p v-for="a in step.approvers" :key="a.id" class="row" style="margin-top: 6px">
        <b>{{ a.nickname || a.account_no }}</b>
        <el-tag size="small" type="info">{{ a.identity_label || '业委会成员' }}</el-tag>
        <el-button size="small" link @click="$emit('remove-approver', index, a.id)">移除</el-button>
      </p>
      <UserPicker :model-value="null" placeholder="搜索并添加审批人" @change="(u) => $emit('add-approver', index, u)" />
    </div>
  </div>
</template>

<script setup>
import UserPicker from './UserPicker.vue'

defineProps({ steps: { type: Array, required: true } })
defineEmits(['add', 'remove', 'move', 'add-approver', 'remove-approver'])
</script>
