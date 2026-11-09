import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import App from './App.vue'
import router from './router'
import './shared/style.css'
import './theme/generated/themes.css'
import { detectLowEnd } from './theme/apply'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
detectLowEnd()
app.mount('#app')
