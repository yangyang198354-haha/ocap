<!-- MOD-149 / REQ-FUNC-246：决议参与人列表（昵称 + 头像 + 参与时间；不含投票选项、手机号、真实姓名）
     AC-270-01：点击头像或昵称进入该用户 profile 页（后端提供 user_id） -->
<template>
  <div class="participant-list">
    <p v-if="mode === 'DESIGNATED'" class="muted">无表决参与人</p>
    <template v-else>
      <p class="participant-count">已参与 {{ items.length }} 人</p>
      <p v-if="!items.length" class="muted">暂无人参与</p>
      <ul v-else class="participant-items">
        <li v-for="(p, index) in items" :key="index" class="participant-item">
          <RouterLink v-if="p.user_id" :to="`/users/${p.user_id}/profile`" class="participant-person">
            <AuthImage v-if="p.avatar_url" :src="p.avatar_url" :alt="p.display_name" :size="32" class="participant-avatar" />
            <span v-else class="participant-avatar participant-avatar-default" aria-hidden="true">{{ initial(p.display_name) }}</span>
            <span class="participant-name">{{ p.display_name }}</span>
          </RouterLink>
          <template v-else>
            <AuthImage v-if="p.avatar_url" :src="p.avatar_url" :alt="p.display_name" :size="32" class="participant-avatar" />
            <span v-else class="participant-avatar participant-avatar-default" aria-hidden="true">{{ initial(p.display_name) }}</span>
            <span class="participant-name">{{ p.display_name }}</span>
          </template>
          <span class="muted mono">{{ formatDateTime(p.voted_at) }}</span>
        </li>
      </ul>
    </template>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router'
import AuthImage from './AuthImage.vue'
import { formatDateTime } from '@/shared/format'

defineProps({
  items: { type: Array, default: () => [] },
  mode: { type: String, default: 'HALF_MAJORITY' }
})

const initial = (name) => String(name || '?').slice(0, 1)
</script>

<style scoped>
.participant-items { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.participant-item { display: flex; align-items: center; gap: 10px; }
.participant-person { display: inline-flex; align-items: center; gap: 10px; color: inherit; text-decoration: none; }
.participant-person:hover .participant-name { text-decoration: underline; }
.participant-avatar { width: 32px; height: 32px; flex: none; border-radius: 50%; }
.participant-avatar-default {
  display: inline-flex; align-items: center; justify-content: center; font-size: 14px;
  color: var(--muted); background: var(--glass); border: 1px solid var(--line);
}
.participant-count { margin: 0; font-weight: 650; }
</style>
