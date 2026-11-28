import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import App from './App.vue'
import router from './router'
import './shared/style.css'
import './theme/generated/themes.css'
import './brand/brand.css'
import './brand/auth-layout.css'
import './brand/auth-motion.css'
import './shared/buttons.css'
import { detectLowEnd } from './theme/apply'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
detectLowEnd()
app.mount('#app')
