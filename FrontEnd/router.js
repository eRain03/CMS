import { createRouter, createWebHashHistory } from 'vue-router'

// 原有页面
import HomeView from './HomeView.vue'
import FarmerView from './FarmerView.vue'
import SlaughterhouseView from './SlaughterhouseView.vue'
import LoginView from './LoginView.vue'
import NotificationsView from './NotificationsView.vue'
import MarketView from './MarketView.vue'
import MatchingCenter from './MatchingCenter.vue'

// ✅ 新增：称重和结算页面
import WeighingView from './WeighingView.vue'
import FinalizeView from './FinalizeView.vue'

const routes = [
  // --- 前台页面 ---
  { path: '/', name: 'home', component: HomeView },
  { path: '/farmer', name: 'farmer', component: FarmerView },
  { path: '/slaughterhouse', name: 'slaughterhouse', component: SlaughterhouseView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/notifications', name: 'notifications', component: NotificationsView },
  { path: '/market', name: 'market', component: MarketView },
  { path: '/matching', name: 'MatchingCenter', component: MatchingCenter },

  // ✅ 新增路由
  {
    path: '/weighing/:id',
    name: 'weighing',
    component: WeighingView,
    meta: { requiresAuth: true }
  },
  {
    path: '/finalize/:id',
    name: 'finalize',
    component: FinalizeView,
    meta: { requiresAuth: true }
  },

  // --- 后台页面 (Admin) ---
  {
    path: '/admin',
    component: () => import('./admin/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      { path: 'logs', component: () => import('./admin/LogsView.vue') },
      { path: 'data', component: () => import('./admin/DataView.vue') },
      { path: 'dashboard', component: () => import('./admin/DashboardView.vue') },
      { path: 'users', component: () => import('./admin/UsersView.vue') },
      { path: 'listings', component: () => import('./admin/ListingsView.vue') }
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

  // Admin 路由检查
  if (to.matched.some(record => record.meta.requiresAdmin) || to.path.startsWith('/admin')) {
    if (!token || role !== 'admin') {
      if (to.name !== 'login') {
        return next('/login')
      }
    }
  }

  // ✅ 新增：普通用户路由检查
  if (to.meta.requiresAuth && !token) {
    return next('/login')
  }

  next()
})

export default router