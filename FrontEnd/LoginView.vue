<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isRegister = ref(false) // 默认为登录模式
const loading = ref(false)
const msg = ref('')

// 定义表单数据结构
const form = reactive({
  username: '',
  password: '',
  // 新增字段
  email: '',
  firstName: '',
  lastName: '',
  phone: '',
  address: '',
  taxId: '', // CPF/CNPJ
  ie: ''     // IE
})

const API_BASE = 'http://43.248.188.75:38939' // 记得换成你的 VPS 地址

const handleAuth = async () => {
  msg.value = ''

  // 1. 基础校验
  if (!form.username || !form.password) {
    return alert('Username and Password are required.')
  }

  // 注册模式下的额外校验
  if (isRegister.value) {
    if (!form.email || !form.firstName || !form.lastName || !form.phone || !form.address) {
      return alert('Please fill in all required fields (marked with *).')
    }
  }

  loading.value = true

  try {
    if (isRegister.value) {
      // --- 注册逻辑 (保持不变) ---
      const payload = {
        username: form.username,
        password: form.password,
        email: form.email,
        first_name: form.firstName,
        last_name: form.lastName,
        phone: form.phone,
        address: form.address,
        tax_id: form.taxId || null,
        ie: form.ie || null
      }

      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Register failed')
      }

      msg.value = 'Account created! Please log in.'
      isRegister.value = false
      form.password = ''

    } else {
      // --- 登录逻辑 (已修改) ---
      const formData = new URLSearchParams()
      formData.append('username', form.username)
      formData.append('password', form.password)

      const res = await fetch(`${API_BASE}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      })

      if (!res.ok) throw new Error('Invalid credentials')

      const data = await res.json()

      // ✅ 1. 存储 Token 和 身份信息
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('role', data.role)       // 关键：存下角色
      localStorage.setItem('username', data.username) // 可选：存下用户名

      // ✅ 2. 根据角色进行路由跳转
      if (data.role === 'admin') {
        router.push('/admin/dashboard') // 管理员 -> 后台
      } else {
        router.push('/') // 普通用户 -> 首页
      }
    }
  } catch (e) {
    console.error(e)
    msg.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-card" :class="{ wide: isRegister }">

      <div class="header-section">
        <h2>{{ isRegister ? 'Create Account' : 'Welcome Back' }}</h2>
        <p class="sub-text">{{ isRegister ? 'Join the marketplace today' : 'Login to manage listings' }}</p>
      </div>

      <div v-if="!isRegister" class="form-body">
        <div class="input-group">
          <label>Username</label>
          <input v-model="form.username" placeholder="Enter username" />
        </div>
        <div class="input-group">
          <label>Password</label>
          <input v-model="form.password" type="password" placeholder="Enter password" @keyup.enter="handleAuth" />
        </div>
      </div>

      <div v-else class="form-body register-grid">

        <div class="full-width section-label">Account Info</div>

        <div class="input-group">
          <label>Username *</label>
          <input v-model="form.username" placeholder="Unique username" />
        </div>
        <div class="input-group">
          <label>Password *</label>
          <input v-model="form.password" type="password" placeholder="Secure password" />
        </div>

        <div class="full-width section-label">Personal Details</div>

        <div class="input-group">
          <label>First Name *</label>
          <input v-model="form.firstName" placeholder="e.g. Joao" />
        </div>
        <div class="input-group">
          <label>Last Name *</label>
          <input v-model="form.lastName" placeholder="e.g. Silva" />
        </div>

        <div class="input-group full-width">
          <label>Email Address *</label>
          <input v-model="form.email" type="email" placeholder="name@company.com" />
        </div>

        <div class="full-width section-label">Contact & Location</div>

        <div class="input-group">
          <label>Phone *</label>
          <input v-model="form.phone" placeholder="+55 11 99999-9999" />
        </div>
        <div class="input-group">
          <label>Address *</label>
          <input v-model="form.address" placeholder="Street, City - State" />
        </div>

        <div class="full-width section-label optional">Business Info (Optional)</div>

        <div class="input-group">
          <label>CPF / CNPJ</label>
          <input v-model="form.taxId" placeholder="Tax ID" />
        </div>
        <div class="input-group">
          <label>IE (Inscrição Estadual)</label>
          <input v-model="form.ie" placeholder="State Registration" />
        </div>

      </div>

      <div class="action-section">
        <p class="error" v-if="msg">{{ msg }}</p>

        <button @click="handleAuth" :disabled="loading" class="btn-main">
          {{ loading ? 'Processing...' : (isRegister ? 'Register Now' : 'Sign In') }}
        </button>

        <div class="toggle-link" @click="isRegister = !isRegister">
          {{ isRegister ? 'Already have an account? Login' : 'New here? Create an account' }}
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  padding-top: 60px;
  background-color: #f8f9fa;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
}

.auth-card {
  width: 100%;
  max-width: 360px;
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
  border: 1px solid #eee;
  transition: max-width 0.3s ease;
  height: fit-content;
}

/* 注册时卡片变宽，容纳双列 */
.auth-card.wide {
  max-width: 600px;
}

.header-section { text-align: center; margin-bottom: 30px; }
.header-section h2 { margin: 0; color: #2c3e50; font-weight: 600; }
.sub-text { color: #888; font-size: 0.9rem; margin-top: 5px; }

/* 表单布局 */
.register-grid {
  display: grid;
  grid-template-columns: 1fr 1fr; /* 双列 */
  gap: 15px;
}

/* 手机端强制单列 */
@media (max-width: 600px) {
  .register-grid { grid-template-columns: 1fr; }
}

.full-width { grid-column: 1 / -1; }

.section-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #95a5a6;
  font-weight: 600;
  border-bottom: 1px solid #eee;
  padding-bottom: 5px;
  margin-top: 15px;
  margin-bottom: 5px;
}
.section-label.optional { color: #27ae60; }

.input-group { display: flex; flex-direction: column; text-align: left; }
.input-group label { font-size: 0.85rem; font-weight: 500; margin-bottom: 5px; color: #34495e; }
.input-group input {
  padding: 10px; border: 1px solid #ddd; border-radius: 6px;
  font-size: 0.95rem; transition: border-color 0.2s;
}
.input-group input:focus { border-color: #2c3e50; outline: none; }

.action-section { margin-top: 30px; text-align: center; }
.btn-main {
  width: 100%; padding: 12px; background: #2c3e50; color: white;
  border: none; border-radius: 6px; cursor: pointer; font-size: 1rem; font-weight: 500;
  transition: background 0.2s;
}
.btn-main:hover { background: #34495e; }
.btn-main:disabled { background: #ccc; cursor: not-allowed; }

.error { color: #c0392b; font-size: 0.9rem; margin-bottom: 15px; background: #ffebee; padding: 8px; border-radius: 4px; }

.toggle-link { margin-top: 20px; font-size: 0.9rem; color: #666; cursor: pointer; text-decoration: underline; }
.toggle-link:hover { color: #2c3e50; }
</style>