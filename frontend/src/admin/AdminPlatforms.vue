<template>
  <div class="page">
    <h2>平台账户</h2>
    <el-card v-for="item in platforms" :key="item.platform" style="margin-bottom: 12px">
      <div class="row" style="justify-content: space-between">
        <strong>{{ item.label }}</strong>
        <el-tag v-if="item.account" :type="item.account.auth_status === 'EXPIRED' ? 'danger' : 'success'">
          {{ authText(item.account.auth_status) }}
        </el-tag>
        <el-tag v-else type="info">未配置</el-tag>
      </div>
      <el-alert v-if="item.platform === 'wechat_mp'" type="info" :closable="false" show-icon
                style="margin-top: 8px"
                title="保存 AppID 和 AppSecret 后由服务器自动获取令牌；需在公众号后台把本服务器的出口 IP 加入 IP 白名单，否则无法获取令牌。" />
      <el-alert v-if="item.account && item.account.auth_status === 'EXPIRED'" type="error" :closable="false"
                show-icon style="margin-top: 8px" title="认证已失效，请重新录入认证信息" />
      <div v-if="item.account" class="row" style="margin-top: 8px">
        <span>账户：{{ item.account.display_name }}</span>
        <el-input v-model="edit[item.platform].display_name" placeholder="新名称" style="width: 180px" />
        <el-input v-for="field in item.credential_fields" :key="field.key"
                  v-model="edit[item.platform].credentials[field.key]"
                  :placeholder="item.account.secret_saved?.[field.key]
                    ? `${field.label}（已保存，输入新值可覆盖）` : `新的 ${field.label}`"
                  style="width: 260px" show-password />
        <el-button size="small" @click="update(item)">保存</el-button>
        <el-button size="small" type="danger" @click="remove(item)">删除</el-button>
      </div>
      <div v-else class="row" style="margin-top: 8px">
        <el-input v-model="edit[item.platform].display_name" placeholder="账户名称" style="width: 180px" />
        <el-input v-for="field in item.credential_fields" :key="field.key"
                  v-model="edit[item.platform].credentials[field.key]"
                  :placeholder="field.label" style="width: 220px" show-password />
        <el-button size="small" type="primary" @click="create(item)">添加账户</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'

const platforms = ref([])
const edit = reactive({})

function authText(value) {
  return { NORMAL: '正常', EXPIRED: '失效', UNSET: '未设置' }[value] || value
}
function ensure(platform) {
  if (!edit[platform]) edit[platform] = { display_name: '', credentials: {} }
  return edit[platform]
}
async function load() {
  platforms.value = await admin.platformAccounts()
  platforms.value.forEach((item) => {
    ensure(item.platform)
    item.credential_fields.forEach((field) => {
      if (edit[item.platform].credentials[field.key] === undefined) {
        edit[item.platform].credentials[field.key] = ''
      }
    })
  })
}
async function create(item) {
  const state = edit[item.platform]
  try {
    await admin.createPlatformAccount({
      platform: item.platform, display_name: state.display_name, credentials: state.credentials
    })
    ElMessage.success('已添加')
    await load()
  } catch (err) {
    ElMessage.error(err.message || '添加失败')
  }
}
async function update(item) {
  const state = edit[item.platform]
  const credentials = Object.fromEntries(Object.entries(state.credentials).filter(([, value]) => value))
  try {
    await admin.updatePlatformAccount(item.account.id, {
      display_name: state.display_name || undefined,
      credentials: Object.keys(credentials).length ? credentials : undefined
    })
    ElMessage.success('已保存')
    await load()
  } catch (err) {
    ElMessage.error(err.message || '保存失败')
  }
}
async function remove(item) {
  try {
    await ElMessageBox.confirm(`确认删除「${item.label}」账户？`, '删除确认', { type: 'warning' })
  } catch { return }
  await admin.deletePlatformAccount(item.account.id)
  await load()
}
onMounted(load)
</script>
