import { createApp } from 'vue'
import App from './App.vue'
import router from './router.js' 

const app = createApp(App)
app.use(router) // <--- 这一行必须有，否则 RouterLink 标签会报错
app.mount('#app')