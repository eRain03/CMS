import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',    // 允许局域网访问（可选）
    port: 3000          // 你可以改成 5173、8080 随便
  }
})
