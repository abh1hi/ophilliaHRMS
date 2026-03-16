<template>
  <v-app>
    <!-- Login screen -->
    <LoginPage v-if="!user" @login="onLogin" />

    <!-- Main app shell -->
    <template v-else>
      <v-main style="background:#FFFBF5;">
        <DashboardPage  v-if="page === 'dashboard'"  :employee="user" @navigate="page = $event" />
        <AttendancePage v-if="page === 'attendance'" :employee="user" />
        <LeavePage      v-if="page === 'leave'"      :employee="user" />
        <ProfilePage    v-if="page === 'profile'"    :employee="user" @logout="onLogout" />
      </v-main>

      <!-- M3 Bottom Navigation Bar — Saffron active indicator -->
      <v-bottom-navigation
        v-model="navIndex"
        color="primary"
        bg-color="surface"
        elevation="0"
        style="border-top: 1px solid rgba(255,153,51,0.18); height:68px;"
        grow
      >
        <v-btn
          v-for="tab in navTabs"
          :key="tab.key"
          :id="'nav-' + tab.key"
          :active="page === tab.key"
          @click="page = tab.key"
          style="min-width:0;"
        >
          <!-- M3 active pill indicator -->
          <v-icon :size="page === tab.key ? 24 : 22">{{ tab.icon }}</v-icon>
          <span class="nav-lbl">{{ tab.label }}</span>
        </v-btn>
      </v-bottom-navigation>
    </template>
  </v-app>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import LoginPage     from './pages/LoginPage.vue'
import DashboardPage from './pages/DashboardPage.vue'
import AttendancePage from './pages/AttendancePage.vue'
import LeavePage     from './pages/LeavePage.vue'
import ProfilePage   from './pages/ProfilePage.vue'
import { saveTokens, clearTokens } from './services/api'

type Page = 'dashboard' | 'attendance' | 'leave' | 'profile'

const user = ref<any>(null)
const page = ref<Page>('dashboard')

const navTabs = [
  { key: 'dashboard',  icon: 'mdi-home-outline',              label: 'Home'       },
  { key: 'attendance', icon: 'mdi-clipboard-check-outline',   label: 'Attendance' },
  { key: 'leave',      icon: 'mdi-calendar-multiselect',      label: 'Leave'      },
  { key: 'profile',    icon: 'mdi-account-circle-outline',    label: 'Profile'    },
] as const

const navIndex = computed({
  get: () => navTabs.findIndex(t => t.key === page.value),
  set: (i) => { page.value = navTabs[i]?.key as Page ?? 'dashboard' },
})

function onLogin(data: any) {
  user.value = data
  if (data.access_token) saveTokens(data.access_token, data.refresh_token ?? '')
  page.value = 'dashboard'
}

function onLogout() {
  user.value = null
  clearTokens()
  page.value = 'dashboard'
}
</script>
