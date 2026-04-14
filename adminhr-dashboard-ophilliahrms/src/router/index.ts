import { createRouter, createWebHistory } from 'vue-router'
import { getToken, clearTokens } from '../services/http'
import { decodeToken } from '../services/auth.service'

const routes = [
  {
    path: '/',
    name: 'Login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true }
  },
  {
    path: '/select-company',
    name: 'SelectCompany',
    component: () => import('../views/CompanySelectionView.vue'),
    meta: { requiresAuth: true, roles: ['super_admin'] }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/payroll',
    name: 'Payroll',
    component: () => import('../views/PayrollView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'hr', 'super_admin'] }
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('../views/OnboardingView.vue'),
    meta: { requiresAuth: true, roles: ['admin', 'super_admin', 'hr'] }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  if (to.meta.public) return next()

  const token = getToken()
  if (!token) {
    clearTokens()
    return next('/')
  }

  const claims = decodeToken(token)
  if (!claims || claims.exp * 1000 < Date.now()) {
    clearTokens()
    return next('/')
  }

  // Role-restricted routes
  const allowedRoles = to.meta.roles as string[] | undefined
  if (allowedRoles && !allowedRoles.includes(claims.role)) {
    return next('/dashboard')
  }

  next()
})

export default router
