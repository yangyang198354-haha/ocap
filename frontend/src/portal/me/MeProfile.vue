<!-- MOD-122：个人资料页（自 Me.vue 原 29-47、160-194 行迁移）；保存后刷新 auth.me 使右上角昵称即时更新（AC-212-05）
     MOD-163：控件垂直对齐（REQ-FUNC-255）、签名档（REQ-FUNC-263）、实名展示开关（REQ-FUNC-262）、头像 5 MB（MOD-156）
     MOD-178：绑定手机/设置密码/邮箱验证/账号注销收敛为本页 Tab，不再直接出现在右上角下拉菜单 -->
<template>
  <div class="page">
    <el-tabs v-model="activeTab" class="me-account-tabs" @tab-change="onTabChange">
      <el-tab-pane label="个人资料" name="profile">
        <div class="card">
          <h3 class="title">个人资料</h3>
          <div class="row profile-row">
            <el-input v-model="profile.nickname" placeholder="昵称" style="width: 240px" />
            <el-select v-model="profile.gender" placeholder="性别" clearable style="width: 120px">
              <el-option label="未知" :value="0" /><el-option label="男" :value="1" /><el-option label="女" :value="2" />
            </el-select>
            <el-date-picker v-model="profile.birthday" type="date" value-format="YYYY-MM-DD" placeholder="生日（选填）" style="width: 180px" />
            <el-button type="primary" @click="saveProfile">保存</el-button>
          </div>
          <p class="muted" style="margin-top: 10px">手机号：{{ profile.phone || '未绑定' }}；邮箱：{{ profile.email || '未填写' }}</p>
          <div class="row" style="margin-top: 8px">
            <AuthImage :src="profile.avatar_url" alt="默认头像" :size="64" />
            <el-upload :show-file-list="false" :http-request="uploadAvatar" :before-upload="checkAvatar" accept=".jpg,.jpeg,.png">
              <el-button>更换头像</el-button>
            </el-upload>
            <span class="muted">jpg/png，不超过 5 MB</span>
          </div>
        </div>

        <div class="card">
          <h4 class="title">签名档</h4>
          <el-input v-model="profile.signature" type="textarea" :rows="3" maxlength="100" show-word-limit
                    placeholder="写一句自我介绍（不超过 100 字）" />
          <div class="row" style="margin-top: 10px">
            <el-button type="primary" @click="saveSignature">保存签名档</el-button>
            <el-button link type="primary" @click="openMyProfile">查看我的主页</el-button>
          </div>
        </div>

        <div class="card">
          <h4 class="title">实名展示</h4>
          <div class="row">
            <el-switch v-model="profile.real_name_visible" :disabled="!canShowRealName" @change="saveRealNameVisible" />
            <span v-if="canShowRealName" class="muted">
              {{ profile.real_name_visible ? `主页将展示实名：${profile.real_name || '（未取到清册姓名）'}` : '主页仅展示昵称' }}
            </span>
            <span v-else class="muted">仅已验证产权业主可设置</span>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="绑定手机" name="phone" lazy>
        <MePhone />
      </el-tab-pane>
      <el-tab-pane label="设置密码" name="password" lazy>
        <MePassword />
      </el-tab-pane>
      <el-tab-pane label="邮箱验证" name="email" lazy>
        <MeEmail />
      </el-tab-pane>
      <el-tab-pane label="账号注销" name="cancel" lazy>
        <MeCancel />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { attachmentApi, meApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import AuthImage from '../parts/AuthImage.vue'
import { useProfile } from './useProfile'
import MePhone from './MePhone.vue'
import MePassword from './MePassword.vue'
import MeEmail from './MeEmail.vue'
import MeCancel from './MeCancel.vue'

const props = defineProps({ initialTab: { type: String, default: 'profile' } })

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const { profile, loadProfile } = useProfile()
const AVATAR_MAX_BYTES = 5 * 1024 * 1024

// Tab 与地址一一对应，便于深链与浏览器前进后退（旧地址 /me/phone 等继续可用）
const TAB_PATHS = {
  profile: '/me/profile',
  phone: '/me/phone',
  password: '/me/password',
  email: '/me/email',
  cancel: '/me/cancel'
}
const activeTab = ref(TAB_PATHS[props.initialTab] ? props.initialTab : 'profile')

watch(() => props.initialTab, (name) => {
  if (TAB_PATHS[name]) activeTab.value = name
})

function onTabChange(name) {
  const target = TAB_PATHS[name]
  if (target && target !== route.path) router.push(target)
}

// AC-271-03：由后端按有效产权认证判定，避免业委会成员因最高身份为职务而被误禁用
const canShowRealName = computed(() => Boolean(profile.can_show_real_name))

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

async function saveSignature() {
  try {
    Object.assign(profile, await meApi.updateProfile({ signature: profile.signature || '' }))
    ElMessage.success('签名档已保存')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function saveRealNameVisible(value) {
  try {
    Object.assign(profile, await meApi.updateProfile({ real_name_visible: Boolean(value) }))
    ElMessage.success('已保存')
  } catch (e) {
    profile.real_name_visible = !value
    ElMessage.error(errorText(e))
  }
}

function openMyProfile() {
  if (profile.id) router.push(`/users/${profile.id}/profile`)
}

// 上传前预校验类型与大小（服务端校验仍为最终防线，C-18）
function checkAvatar(file) {
  const okType = ['image/jpeg', 'image/png'].includes(file.type) || /\.(jpe?g|png)$/i.test(file.name || '')
  if (!okType) {
    ElMessage.error('头像仅支持 jpg/png 格式')
    return false
  }
  if (file.size > AVATAR_MAX_BYTES) {
    ElMessage.error('头像不能超过 5 MB')
    return false
  }
  return true
}

async function uploadAvatar({ file }) {
  try {
    const uploaded = await attachmentApi.upload(file, 'AVATAR')
    await meApi.updateProfile({ avatar_attachment_id: uploaded.id })
    await loadProfile()
    await auth.fetchMe().catch(() => null)
    ElMessage.success('头像已更新')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}
</script>

<style scoped>
.profile-row { align-items: center; gap: 8px; flex-wrap: wrap; }
.profile-row :deep(.el-input__wrapper),
.profile-row :deep(.el-select__wrapper) { min-height: 32px; }
/* 子页自带 .page 内边距，嵌入 Tab 后去掉，避免双层留白 */
.me-account-tabs :deep(.el-tab-pane > .page) { padding: 0; margin: 0; max-width: none; }
</style>
