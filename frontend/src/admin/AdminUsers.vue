<template>
  <div class="page">
    <div class="card">
      <div class="row" style="justify-content: space-between">
        <h3 class="title" style="margin: 0">管理员账号</h3>
        <el-button type="primary" @click="showCreate = true">新建管理员</el-button>
      </div>
      <el-table :data="admins" size="small">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="账号" width="160" />
        <el-table-column label="启用" width="90">
          <template #default="{ row }">{{ yesNo(row.is_active) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="reset(row)">重置密码</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="card">
      <h3 class="title">注册用户</h3>
      <el-input v-model="keyword" placeholder="昵称 / 手机号 / 账号 / 实名" style="max-width: 260px" @change="resetAndLoad" />
      <el-table :data="users" size="small" style="margin-top: 10px">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="account_no" label="账号" width="150" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="nickname" label="昵称" min-width="120" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">{{ statusLabel('account', row.status) }}</template>
        </el-table-column>
        <el-table-column prop="identity_label" label="身份" width="110" />
        <el-table-column label="认证" width="130">
          <template #default="{ row }">
            {{ row.certified_units > 0 ? `已认证（${row.certified_units} 套）` : '未认证' }}
          </template>
        </el-table-column>
        <el-table-column label="实名" width="140">
          <template #default="{ row }">
            {{ row.real_names?.length ? row.real_names.join('、') : '—' }}
          </template>
        </el-table-column>
        <el-table-column label="上次登录" width="160">
          <template #default="{ row }">{{ formatDateTime(row.last_login_at) || '从未登录' }}</template>
        </el-table-column>
      </el-table>
      <PagerBar :total="total" :page="page" :page-size="pageSize" @change="gotoPage" />
    </div>

    <el-dialog v-model="showCreate" title="新建管理员" width="420px">
      <el-input v-model="createForm.username" placeholder="账号" />
      <el-input v-model="createForm.password" type="password" placeholder="初始密码" show-password style="margin-top: 8px" />
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="createAdmin">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { admin } from '@/shared/api'
import PagerBar from '@/shared/PagerBar.vue'
import { errorText, formatDateTime } from '@/shared/format'
import { statusLabel, yesNo } from '@/shared/labels'
import { usePaging } from '@/shared/usePaging'

const admins = ref([])
const keyword = ref('')
const showCreate = ref(false)
const createForm = reactive({ username: '', password: '' })
// 搜索关键词在翻页时保持不变（REQ-FUNC-152）
const filters = computed(() => ({ q: keyword.value || undefined }))
const { items: users, total, page, pageSize, reload, goto, resetAndLoad: pagingReset } = usePaging({
  fetch: (params) => admin.users(params), filters
})

async function load() {
  try {
    const [adminData] = await Promise.all([admin.admins(), reload()])
    admins.value = adminData.results || adminData || []
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function resetAndLoad() {
  try {
    await pagingReset()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function gotoPage(n) {
  try {
    await goto(n)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function createAdmin() {
  try {
    await admin.createAdmin({ ...createForm })
    showCreate.value = false
    ElMessage.success('已创建')
    load()
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function reset(row) {
  try {
    const { value } = await ElMessageBox.prompt('输入新密码', `重置 ${row.username} 的密码`, { inputType: 'password' })
    await admin.resetPassword(row.id, value)
    ElMessage.success('已重置')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(errorText(e))
  }
}

onMounted(load)
</script>
