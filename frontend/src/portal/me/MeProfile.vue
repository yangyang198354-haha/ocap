<!-- MOD-122：个人资料页（自 Me.vue 原 29-47、160-194 行迁移）；保存后刷新 auth.me 使右上角昵称即时更新（AC-212-05） -->
<template>
  <div class="page">
    <div class="card">
      <h3 class="title">个人资料</h3>
      <div class="row">
        <el-input v-model="profile.nickname" placeholder="昵称" style="max-width: 240px" />
        <el-select v-model="profile.gender" placeholder="性别" clearable style="width: 120px">
          <el-option label="未知" :value="0" /><el-option label="男" :value="1" /><el-option label="女" :value="2" />
        </el-select>
        <el-date-picker v-model="profile.birthday" type="date" value-format="YYYY-MM-DD" placeholder="生日（选填）" style="max-width: 180px" />
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </div>
      <p class="muted" style="margin-top: 10px">手机号：{{ profile.phone || '未绑定' }}；邮箱：{{ profile.email || '未填写' }}</p>
      <div class="row">
        <AuthImage :src="profile.avatar_url" alt="暂无头像" :size="64" />
        <el-upload :show-file-list="false" :http-request="uploadAvatar" :before-upload="checkAvatar" accept=".jpg,.jpeg,.png">
          <el-button>更换头像</el-button>
        </el-upload>
        <span class="muted">jpg/png，不超过 2 MB</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { attachmentApi, meApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import AuthImage from '../parts/AuthImage.vue'
import { useProfile } from './useProfile'

const auth = useAuthStore()
const { profile, loadProfile } = useProfile()
const AVATAR_MAX_BYTES = 2 * 1024 * 1024

onMounted(loadProfile)

async function saveProfile() {
  try {
    Object.assign(profile, await meApi.updateProfile({
      nickname: profile.nickname, gender: profile.gender, birthday: profile.birthday || null
    }))
    ElMessage.success('已保存')
    await auth.fetchMe().catch(() => null)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

// 上传前预校验类型与大小（服务端校验仍为最终防线，C-18）
function checkAvatar(file) {
  const okType = ['image/jpeg', 'image/png'].includes(file.type) || /\.(jpe?g|png)$/i.test(file.name || '')
  if (!okType) {
    ElMessage.error('头像仅支持 jpg/png 格式')
    return false
  }
  if (file.size > AVATAR_MAX_BYTES) {
    ElMessage.error('头像不能超过 2 MB')
    return false
  }
  return true
}

async function uploadAvatar({ file }) {
  try {
    const uploaded = await attachmentApi.upload(file, 'AVATAR')
    await meApi.updateProfile({ avatar_attachment_id: uploaded.id })
    await loadProfile()
    ElMessage.success('头像已更新')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}
</script>
