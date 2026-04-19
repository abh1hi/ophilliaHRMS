import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.store'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    redirect: '/dashboard',
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  if (to.meta.public) return next()

  const auth = useAuthStore()

  if (!auth.isAuthenticated) {
    return next('/login')
  }

  // This portal is super_admin only — block all other roles
  if (auth.role !== 'super_admin') {
    auth.logout()
    return next('/login')
  }

  next()
})

export default router
