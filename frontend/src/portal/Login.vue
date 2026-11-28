<template>
  <AuthShell surface="portal">
    <div class="card auth-form-card">
      <el-tabs v-model="tab">
        <el-tab-pane label="验证码" name="code">
          <form v-if="tab === 'code'" id="portal-sms-login" method="post" @submit.prevent="loginCode">
            <el-input id="portal-sms-phone" v-model="form.phone" name="phone" type="tel" autocomplete="tel" placeholder="手机号" aria-label="手机号" maxlength="11" />
            <div class="row" style="margin-top: 10px">
              <el-input id="portal-sms-code" v-model="form.code" name="sms_code" inputmode="numeric" autocomplete="one-time-code" placeholder="验证码" aria-label="短信验证码" maxlength="6" style="flex: 1" />
              <el-button :disabled="counting > 0" @click="sendCode">{{ counting ? `${counting}s` : '获取验证码' }}</el-button>
            </div>
            <el-checkbox v-model="form.remember" style="margin-top: 10px">记住我（15 天）</el-checkbox>
            <el-button type="primary" native-type="submit" style="width: 100%; margin-top: 12px" :loading="loading">登录</el-button>
          </form>
        </el-tab-pane>
        <el-tab-pane label="密码" name="password">
          <form v-if="tab === 'password'" id="portal-password-login" method="post" @submit.prevent="loginPassword">
            <el-input id="portal-login-identifier" v-model="form.identifier" name="identifier" autocomplete="username" placeholder="账号或手机号" aria-label="账号或手机号" />
            <el-input id="portal-login-password" v-model="form.password" name="password" type="password" autocomplete="current-password" placeholder="密码" aria-label="密码" style="margin-top: 10px" show-password />
            <el-checkbox v-model="form.remember" style="margin-top: 10px">记住我（15 天）</el-checkbox>
            <el-button type="primary" native-type="submit" style="width: 100%; margin-top: 12px" :loading="loading">登录</el-button>
          </form>
        </el-tab-pane>
        <el-tab-pane label="邮箱" name="email">
          <form v-if="tab === 'email'" id="portal-email-login" method="post" @submit.prevent="loginEmail">
            <el-input id="portal-login-email" v-model="form.email" name="email" inputmode="email" autocomplete="email" placeholder="邮箱" aria-label="邮箱" />
            <div class="row" style="margin-top: 10px">
              <el-input id="portal-email-code" v-model="form.emailCode" name="email_code" inputmode="numeric" autocomplete="one-time-code" placeholder="验证码" aria-label="邮箱验证码" maxlength="6" style="flex: 1" />
              <el-button :disabled="counting > 0" @click="sendEmailCode">{{ counting ? `${counting}s` : '获取验证码' }}</el-button>
            </div>
            <el-button type="primary" native-type="submit" style="width: 100%; margin-top: 12px" :loading="loading">登录</el-button>
          </form>
        </el-tab-pane>
      </el-tabs>
      <div class="row" style="justify-content: space-between; margin-top: 14px">
        <router-link to="/register">用户注册</router-link>
        <a v-if="wechatUrl" :href="wechatUrl">微信扫码登录</a>
      </div>
    </div>
  </AuthShell>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authApi } from '@/shared/api'
import { useAuthStore } from '@/stores/auth'
import { errorText } from '@/shared/format'
import { useThemeStore } from '@/theme/store'
import AuthShell from '@/brand/AuthShell.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const themeStore = useThemeStore()
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

async function done(result) {
  auth.setAuth(result.token, result.user)
  // IFC-441：身份未随登录响应返回时先补齐，首页首帧即最终结构，避免游客态二次渲染
  await auth.ensureMe().catch(() => null)
  // 先对账账号级风格再跳转，登录页保持原风格直到新账号风格就绪（ADR-027 第 4 条）
  await themeStore.reconcileAfterLogin()
  router.replace(route.query.redirect || '/')
}

async function run(fn) {
  loading.value = true
  try {
    await done(await fn())
  } catch (e) {
    ElMessage.error(errorText(e))
  } finally {
    loading.value = false
  }
}

const loginCode = () => run(() => authApi.loginByCode(form.phone, form.code, form.remember))
function loginPassword(event) {
  // 密码管理器填入的值可能没有触发 Vue 的 input 事件。
  const fields = event ? new FormData(event.currentTarget) : null
  const identifier = fields?.get('identifier') ?? form.identifier
  const password = fields?.get('password') ?? form.password
  return run(() => authApi.loginByPassword(identifier, password, form.remember))
}
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
