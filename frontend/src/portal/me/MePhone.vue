<!-- MOD-122：手机号页，绑定与更换合一（自 Me.vue 原 49-74、196-243 行迁移；按 profile.phone 空/非空互斥） -->
<template>
  <div class="page">
    <div class="card" v-if="!profile.phone">
      <h3 class="title">绑定手机号</h3>
      <p class="muted">仅微信登录的账号需要先绑定手机号才能做业主认证、注销等操作。若该手机号已注册，两个账号将合并（以该手机号原账号为主）。</p>
      <div class="row">
        <el-input v-model="bind.phone" placeholder="手机号" maxlength="11" style="max-width: 180px" />
        <el-button @click="sendBindCode">发送验证码</el-button>
        <el-input v-model="bind.code" placeholder="验证码" maxlength="6" style="max-width: 140px" />
        <el-button type="primary" @click="bindPhone">绑定</el-button>
      </div>
    </div>

    <div class="card" v-else>
      <h3 class="title">更换手机号</h3>
      <p class="muted">需要原手机号和新手机号各自的验证码。新手机号若已属于其他账号，两个账号将合并（以新手机号原账号为主，身份取高）。</p>
      <div class="row">
        <el-input v-model="change.oldPhone" placeholder="原手机号" maxlength="11" style="max-width: 160px" />
        <el-button @click="sendChangeCode(change.oldPhone)">发送原号验证码</el-button>
        <el-input v-model="change.oldCode" placeholder="原号验证码" maxlength="6" style="max-width: 140px" />
      </div>
      <div class="row" style="margin-top: 8px">
        <el-input v-model="change.newPhone" placeholder="新手机号" maxlength="11" style="max-width: 160px" />
        <el-button @click="sendChangeCode(change.newPhone)">发送新号验证码</el-button>
        <el-input v-model="change.newCode" placeholder="新号验证码" maxlength="6" style="max-width: 140px" />
        <el-button type="primary" @click="changePhone">更换</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { meApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import { useProfile } from './useProfile'

const auth = useAuthStore()
const { profile, loadProfile } = useProfile()
const bind = reactive({ phone: '', code: '' })
const change = reactive({ oldPhone: '', newPhone: '', oldCode: '', newCode: '' })

onMounted(loadProfile)

async function sendCode(purpose, target, tip = '验证码已发送') {
  try {
    await meApi.sendCode(purpose, target)
    ElMessage.success(tip)
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

const sendBindCode = () => sendCode('BIND_PHONE', bind.phone)
const sendChangeCode = (phone) => sendCode('CHANGE_PHONE', phone)

// 合并成功时旧令牌已失效，换用返回的新令牌（IFC-071/072）
async function afterPhoneChange(result) {
  if (result.merged && result.token) {
    auth.setAuth(result.token, null)
    ElMessage.success('账号已合并，已切换到主账号')
  } else {
    const bound = result.auto_bound || []
    if (bound.length) {
      const parts = bound.map((item) => item.specific_part).join('、')
      ElMessage.success(`手机号已绑定，已根据你的手机号自动认证为 ${parts} 的产权业主`)
    } else {
      ElMessage.success('手机号已更新')
    }
  }
  await auth.fetchMe().catch(() => null)
  await loadProfile()
}

async function bindPhone() {
  try {
    await afterPhoneChange(await meApi.bindPhone(bind.phone, bind.code))
    Object.assign(bind, { phone: '', code: '' })
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function changePhone() {
  try {
    await afterPhoneChange(await meApi.changePhone(change.oldPhone, change.newPhone, change.oldCode, change.newCode))
    Object.assign(change, { oldPhone: '', newPhone: '', oldCode: '', newCode: '' })
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}
</script>
