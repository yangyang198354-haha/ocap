<!-- MOD-162 / IFC-375：他人 profile 页（REQ-FUNC-261/262、REQ-NFUNC-052；字段白名单由后端返回） -->
<template>
  <div class="page">
    <div class="card">
      <el-empty v-if="loading" description="加载中…" />
      <template v-else-if="profile">
        <div class="row profile-head">
          <AuthImage :src="profile.avatar_url" alt="默认头像" :size="72" />
          <div class="profile-meta">
            <h3 class="title profile-name" style="margin: 0">{{ profile.nickname || '未设置昵称' }}</h3>
            <div class="profile-tags">
              <span v-if="profile.real_name" class="real-name">
                实名：{{ profile.real_name }}
                <el-tag class="verified-badge" size="small" type="success" effect="plain">✓ 已实名认证</el-tag>
              </span>
              <el-tag class="identity-tag" size="small" type="info">{{ profile.identity?.label || '游客' }}</el-tag>
            </div>
          </div>
          <el-button v-if="profile.is_self" type="primary" plain @click="$router.push('/me/profile')">编辑资料</el-button>
        </div>
        <div class="signature">
          <p class="muted" style="margin: 0 0 6px">签名档</p>
          <p v-if="profile.signature" class="signature-text">{{ profile.signature }}</p>
          <p v-else class="muted">这个人很懒，什么都没写</p>
        </div>
      </template>
      <el-empty v-else description="用户不存在或已注销" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { meApi } from '@/shared/api'
import { errorText } from '@/shared/format'
import AuthImage from './parts/AuthImage.vue'

const route = useRoute()
const profile = ref(null)
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    profile.value = await meApi.userProfile(route.params.user_id)
  } catch (e) {
    profile.value = null
    ElMessage.error(errorText(e))
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.user_id, load)
</script>

<style scoped>
.profile-head { align-items: center; gap: 16px; }
.profile-meta { flex: 1; min-width: 0; }
.profile-tags { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; margin-top: 4px; }
.real-name { display: inline-flex; align-items: center; gap: 6px; color: var(--text); font-weight: 650; font-size: 14px; }
.identity-tag { font-weight: 400; }
.signature { margin-top: 20px; border-top: 1px solid var(--line); padding-top: 14px; }
.signature-text { margin: 0; white-space: pre-wrap; word-break: break-word; }
</style>
