import { createRouter, createWebHashHistory } from 'vue-router'

// 1. 修正引入路径
// ⚠️ 如果你的文件在 src/views 下，必须用 ./ 或者 @/views/
import HomeView from './HomeView.vue'
import FarmerView from './FarmerView.vue'
import SlaughterhouseView from './SlaughterhouseView.vue'
import LoginView from './LoginView.vue'
import NotificationsView from './NotificationsView.vue'
import MarketView from './MarketView.vue'
import MatchingCenter from './MatchingCenter.vue'

const routes = [
  // --- 前台页面 ---
  { path: '/', name: 'home', component: HomeView },
  { path: '/farmer', name: 'farmer', component: FarmerView },
  { path: '/slaughterhouse', name: 'slaughterhouse', component: SlaughterhouseView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/notifications', name: 'notifications', component: NotificationsView },
  { path: '/market', name: 'market', component: MarketView },
  {
    path: '/matching',      // 浏览器访问路径
    name: 'MatchingCenter',
    component: MatchingCenter
  },

  // --- 后台页面 (Admin) ---


  {
    path: '/admin',
    // ⚠️ 修正路径：确保指向 src/views/admin/...
    component: () => import('./admin/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      // 在 admin 的 children 数组里添加
      {
        path: 'logs',
        component: () => import('./admin/LogsView.vue')
      },
      {
        path: 'data',
        component: () => import('./admin/DataView.vue')
      },

      {
        path: 'dashboard',
        component: () => import('./admin/DashboardView.vue')
      },
      {
        path: 'users',
        component: () => import('./admin/UsersView.vue')
      },
      // ✅ 修正：Listings 必须放在这里，才能享受侧边栏布局
      {
        path: 'listings',
        component: () => import('./admin/ListingsView.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 全局路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const role = localStorage.getItem('role')

  if (to.matched.some(record => record.meta.requiresAdmin) || to.path.startsWith('/admin')) {
    if (!token || role !== 'admin') {
      if (to.name !== 'login') {
        // alert('Access Denied: Admins only.') // 建议注释掉弹窗，直接跳转体验更好
        return next('/login')
      }
    }
  }
  next()
})

export default router