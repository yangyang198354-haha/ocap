<template>
  <div class="page">
    <h2>信息公开</h2>
    <el-empty v-if="!items.length" description="暂无公开信息" />
    <div v-for="item in items" :key="item.id" class="list-item">
      <router-link :to="`/info/${item.id}`">{{ item.title }}</router-link>
      <span class="muted">{{ item.published_at }}</span>
      <p class="muted">{{ item.summary }}</p>
    </div>
    <el-pagination v-model:current-page="page" :total="count" :page-size="20" layout="prev, pager, next, total"
                   style="margin-top: 12px" @current-change="load" />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { infoApi } from '@/shared/api'

const items = ref([])
const page = ref(1)
const count = ref(0)

async function load() {
  const data = await infoApi.list({ page: page.value })
  items.value = data.results || []
  count.value = data.count || 0
}
onMounted(load)
</script>
