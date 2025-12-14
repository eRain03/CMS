<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isSidebarOpen = ref(false) // 控制手机端侧边栏开关

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

// 点击菜单链接后自动关闭侧边栏 (提升手机体验)
const navigate = (path) => {
  router.push(path)
  isSidebarOpen.value = false
}

const logout = () => {
  if(confirm('Log out of Admin Console?')) {
    localStorage.removeItem('token')
    localStorage.removeItem('role')
    router.push('/login')
  }
}
</script>

<template>
  <div class="admin-container">

    <header class="mobile-header">
      <button class="menu-btn" @click="toggleSidebar">☰</button>
      <span class="mobile-brand">ADMIN CONSOLE</span>
    </header>

    <div
      class="sidebar-overlay"
      :class="{ show: isSidebarOpen }"
      @click="isSidebarOpen = false"
    ></div>

    <aside class="sidebar" :class="{ open: isSidebarOpen }">
      <div class="sidebar-header">
        <h2>CATTLE ADMIN</h2>
        <small>System Control</small>
      </div>

      <nav class="sidebar-nav">
        <a @click="navigate('/admin/dashboard')" class="nav-item">📊 Dashboard</a>
        <a @click="navigate('/admin/users')" class="nav-item">👥 User Mgmt</a>
        <a @click="navigate('/admin/listings')" class="nav-item">📝 Listings</a>
        <a @click="navigate('/admin/data')" class="nav-item">🗂️ Data & Refs</a>
        <a @click="navigate('/admin/logs')" class="nav-item">⚠️ Error Logs</a>

        <div class="divider"></div>
        <a @click="router.push('/')" class="nav-item link-home">🏠 View Site</a>
      </nav>

      <div class="sidebar-footer">
        <div class="admin-info">Logged in as SuperUser</div>
        <button @click="logout" class="btn-logout">Logout</button>
      </div>
    </aside>

    <main class="main-content">
      <router-view />
    </main>

  </div>
</template>

<style scoped>
/* ================= 基础布局 (Desktop First) ================= */
.admin-container {
  display: flex;
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: #f4f6f8;
}

/* 侧边栏 */
.sidebar {
  width: 260px;
  background: #1e293b;
  color: white;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: transform 0.3s ease;
  z-index: 1000;
  height: 100vh;
  position: sticky;
  top: 0;
}

.sidebar-header { padding: 25px 20px; text-align: center; border-bottom: 1px solid #334155; background: #0f172a; }
.sidebar-header h2 { margin: 0; font-size: 1.2rem; letter-spacing: 1px; color: #fff; }
.sidebar-header small { color: #64748b; font-size: 0.75rem; text-transform: uppercase; }

.sidebar-nav { flex: 1; padding: 20px 0; overflow-y: auto; }
.nav-item {
  display: block; padding: 15px 25px; color: #94a3b8;
  text-decoration: none; transition: 0.2s; cursor: pointer;
  font-size: 0.95rem; border-left: 3px solid transparent;
}
.nav-item:hover, .nav-item.router-link-active {
  background: #334155; color: white; border-left-color: #3b82f6;
}

.divider { height: 1px; background: #334155; margin: 15px 25px; }
.link-home { color: #3b82f6; }

.sidebar-footer { padding: 20px; border-top: 1px solid #334155; background: #0f172a; }
.admin-info { font-size: 0.75rem; color: #64748b; margin-bottom: 10px; text-align: center; }
.btn-logout { width: 100%; padding: 10px; background: #ef4444; border: none; color: white; border-radius: 6px; cursor: pointer; font-weight: 600; }

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 40px;
  overflow-x: hidden; /* 防止表格撑破页面 */
  max-width: 100%;    /* 限制最大宽度 */
}

/* 隐藏手机组件 */
.mobile-header, .sidebar-overlay { display: none; }

/* ================= 📱 手机端适配 (Responsive) ================= */
@media (max-width: 768px) {

  .admin-container { flex-direction: column; }

  /* 1. 显示顶部手机导航 */
  .mobile-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 20px; height: 60px; background: #1e293b; color: white;
    position: sticky; top: 0; z-index: 900; box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  }
  .menu-btn { background: none; border: none; color: white; font-size: 1.5rem; cursor: pointer; }
  .mobile-brand { font-weight: 700; letter-spacing: 1px; }

  /* 2. 侧边栏变为抽屉 */
  .sidebar {
    position: fixed; top: 0; left: 0; bottom: 0;
    transform: translateX(-100%); /* 默认隐藏到左边 */
    width: 260px;
    box-shadow: 4px 0 15px rgba(0,0,0,0.2);
  }
  .sidebar.open { transform: translateX(0); } /* 滑出 */

  /* 3. 遮罩层 */
  .sidebar-overlay {
    display: block; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.5); z-index: 999;
    opacity: 0; pointer-events: none; transition: opacity 0.3s;
  }
  .sidebar-overlay.show { opacity: 1; pointer-events: auto; }

  /* 4. 主内容调整 */
  .main-content { padding: 20px 15px; }
}
</style>