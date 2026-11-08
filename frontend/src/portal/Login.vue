<template>
  <div class="page" style="max-width: 420px; padding-top: 60px">
    <div class="card">
      <h2 class="title">业主委员会 · 登录</h2>
      <el-tabs v-model="tab">
        <el-tab-pane label="验证码" name="code">
          <el-input v-model="form.phone" placeholder="手机号" maxlength="11" />
          <div class="row" style="margin-top: 10px">
            <el-input v-model="form.code" placeholder="验证码" maxlength="6" style="flex: 1" />
            <el-button :disabled="counting > 0" @click="sendCode">{{ counting ? `${counting}s` : '获取验证码' }}</el-button>
          </div>
          <el-checkbox v-model="form.remember" style="margin-top: 10px">记住我（7 天）</el-checkbox>
          <el-button type="primary" style="width: 100%; margin-top: 12px" :loading="loading" @click="loginCode">登录</el-button>
        </el-tab-pane>
        <el-tab-pane label="密码" name="password">
          <el-input v-model="form.identifier" placeholder="手机号 / 邮箱 / 账号" />
          <el-input v-model="form.password" type="password" placeholder="密码" style="margin-top: 10px" show-password />
          <el-checkbox v-model="form.remember" style="margin-top: 10px">记住我（7 天）</el-checkbox>
          <el-button type="primary" style="width: 100%; margin-top: 12px" :loading="loading" @click="loginPassword">登录</el-button>
        </el-tab-pane>
        <el-tab-pane label="邮箱" name="email">
          <el-input v-model="form.email" placeholder="邮箱" />
          <div class="row" style="margin-top: 10px">
            <el-input v-model="form.emailCode" placeholder="验证码" maxlength="6" style="flex: 1" />
            <el-button :disabled="counting > 0" @click="sendEmailCode">{{ counting ? `${counting}s` : '获取验证码' }}</el-button>
          </div>
          <el-button type="primary" style="width: 100%; margin-top: 12px" :loading="loading" @click="loginEmail">登录</el-button>
        </el-tab-pane>
      </el-tabs>
      <div class="row" style="justify-content: space-between; margin-top: 14px">
        <router-link to="/register">手机号注册</router-link>
        <a v-if="wechatUrl" :href="wechatUrl">微信扫码登录</a>
      </div>
      <p class="muted" style="margin-bottom: 0">小程序用户请在微信小程序内使用微信一键登录。</p>
    </div>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const tab = ref('code')
const loading = ref(false)
const counting = ref(0)
const wechatUrl = ref('')
const form = reactive({ phone: '', code: '', identifier: '', password: '', email: '', emailCode: '', remember: false })

function tick() {
  counting.value = Number(sessionStorage.getItem('ocap_code_countdown') || 0)
  if (counting.value <= 0) return
  setTimeout(() => {
    counting.value -= 1
    sessionStorage.setItem('ocap_code_countdown', String(counting.value))
    tick()
  }, 1000)
}

async function sendCode() {
  try {
    await authApi.sendCode(form.phone, 'LOGIN')
    counting.value = 60
    sessionStorage.setItem('ocap_code_countdown', '60')
    tick()
    ElMessage.success('验证码已发送')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

async function sendEmailCode() {
  try {
    await authApi.sendCode(form.email, 'EMAIL_LOGIN', 'EMAIL')
    ElMessage.success('验证码已发送')
  } catch (e) {
    ElMessage.error(errorText(e))
  }
}

function done(result) {
  auth.setAuth(result.token, result.user)
  router.replace(route.query.redirect || '/')
}

async function run(fn) {
  loading.value = true
  try {
    done(await fn())
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    loading.value = false
  }
}

const loginCode = () => run(() => authApi.loginByCode(form.phone, form.code, form.remember))
const loginPassword = () => run(() => authApi.loginByPassword(form.identifier, form.password, form.remember))
const loginEmail = () => run(() => authApi.loginByEmail(form.email, form.emailCode, form.remember))

onMounted(async () => {
  tick()
  try {
    const params = await authApi.wechatWebParams()
    const appid = params.appid || params.app_id
    if (!appid) return
    // redirect_uri 由服务端配置并随参数返回（IFC-028），前端不得自带
    const redirect = encodeURIComponent(params.redirect_uri)
    wechatUrl.value = `https://open.weixin.qq.com/connect/qrconnect?appid=${appid}&redirect_uri=${redirect}&response_type=code&scope=snsapi_login&state=${params.state}#wechat_redirect`
  } catch (e) {
    /* 未配置微信开放平台时隐藏入口 */
  }
})
</script>
