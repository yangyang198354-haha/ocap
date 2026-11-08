<template>
  <div class="page">
    <div class="card" v-if="item">
      <h3 class="title">{{ item.title }}</h3>
      <p class="muted">
        状态：{{ item.status }} · 审批方式：{{ item.approval_mode }}
        <span v-if="item.vote_deadline">· 表决截止：{{ item.vote_deadline }}</span>
      </p>
      <p style="white-space: pre-wrap">{{ item.content }}</p>
      <div class="row" v-if="item.attachments?.length">
        <el-link v-for="a in item.attachments" :key="a.id" :href="apiUrl(`/attachments/${a.id}/download`)" target="_blank">
          {{ a.original_name }}
        </el-link>
      </div>
      <div v-if="item.vote_counts" class="row" style="margin-top: 12px">
        <el-tag>同意 {{ item.vote_counts.agree }}</el-tag>
        <el-tag type="danger">反对 {{ item.vote_counts.disagree }}</el-tag>
        <el-tag type="info">弃权 {{ item.vote_counts.abstain }}</el-tag>
      </div>
      <div class="row" v-if="item.approval_mode === 'HALF_MAJORITY' && item.status === 'PENDING'" style="margin-top: 12px">
        <el-button type="success" @click="vote('AGREE')">同意</el-button>
        <el-button type="danger" @click="vote('DISAGREE')">反对</el-button>
        <el-button @click="vote('ABSTAIN')">弃权</el-button>
      </div>
    </div>
    <div class="card" v-else>
      <el-empty description="决议不存在或无权查看" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { resolutionApi } from '@/shared/api'
import { apiUrl } from '@/shared/http'
import { errorText } from '@/shared/format'

const route = useRoute()
const item = ref(null)

async function load() {
  try {
    item.value = await resolutionApi.detail(route.params.id)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function vote(choice) {
  try {
    await resolutionApi.vote(route.params.id, choice)
    ElMessage.success('已提交意见')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
