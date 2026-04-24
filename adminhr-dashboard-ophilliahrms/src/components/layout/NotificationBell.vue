<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Bell, CheckCheck, X } from 'lucide-vue-next'
import {
  getUnreadCount,
  listNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from '../../services/notification.service'
import type { Notification } from '../../services/notification.service'

const open = ref(false)
const unreadCount = ref(0)
const notifications = ref<Notification[]>([])
const loadingNotifs = ref(false)
const markingAll = ref(false)

let pollTimer: ReturnType<typeof setInterval> | null = null

const notifTypeIcons: Record<string, string> = {
  early_clockout:              '🚪',
  late_request_submitted:      '⏰',
  late_clockin_approved:       '✅',
  break_outside_window:        '☕',
  break_auto_completed:        '🔔',
  schedule_expiry_warning:     '📅',
  auto_clockout:               '🔒',
  off_day_request_submitted:   '📋',
  tasks_pending_reminder:      '📝',
}

function getIcon(type: string) {
  return notifTypeIcons[type] ?? '🔔'
}

function fmtTime(dt: string) {
  const d = new Date(dt)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin}m ago`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24) return `${diffH}h ago`
  return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

async function fetchCount() {
  unreadCount.value = await getUnreadCount()
}

async function openBell() {
  open.value = true
  loadingNotifs.value = true
  try {
    notifications.value = await listNotifications(20)
    unreadCount.value = notifications.value.filter(n => !n.is_read).length
  } finally {
    loadingNotifs.value = false
  }
}

async function dismiss(notif: Notification) {
  if (!notif.is_read) {
    await markNotificationRead(notif.id)
    notif.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
}

async function markAll() {
  markingAll.value = true
  try {
    await markAllNotificationsRead()
    notifications.value.forEach(n => { n.is_read = true })
    unreadCount.value = 0
  } finally {
    markingAll.value = false }
}

onMounted(() => {
  fetchCount()
  pollTimer = setInterval(fetchCount, 30_000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="relative">
    <!-- Bell button -->
    <button
      @click="open ? (open = false) : openBell()"
      :class="[
        'relative flex items-center justify-center w-9 h-9 rounded-lg transition-colors',
        open ? 'bg-slate-100 text-slate-800' : 'text-slate-500 hover:bg-slate-50 hover:text-slate-800'
      ]"
      title="Notifications"
    >
      <Bell class="w-4.5 h-4.5" style="width:18px;height:18px;" />
      <!-- Unread badge -->
      <span
        v-if="unreadCount > 0"
        class="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 bg-rose-500 text-white text-[9px] font-black rounded-full flex items-center justify-center px-1 leading-none shadow"
      >
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <Transition name="drop">
      <div
        v-if="open"
        class="absolute top-11 right-0 w-80 bg-white border border-slate-200 rounded-2xl shadow-xl overflow-hidden z-50"
      >
        <!-- Header -->
        <div class="flex items-center justify-between px-4 py-3 border-b border-slate-100">
          <span class="text-sm font-black text-slate-900">Notifications</span>
          <div class="flex items-center gap-2">
            <button
              v-if="unreadCount > 0"
              @click="markAll"
              :disabled="markingAll"
              class="flex items-center gap-1 text-[10px] font-bold text-indigo-600 hover:text-indigo-700 uppercase tracking-widest disabled:opacity-50"
            >
              <CheckCheck class="w-3 h-3" />
              Mark all read
            </button>
            <button @click="open = false" class="text-slate-400 hover:text-slate-700 transition-colors">
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- List -->
        <div class="max-h-[360px] overflow-y-auto divide-y divide-slate-50">
          <div v-if="loadingNotifs" class="flex items-center justify-center py-10">
            <div class="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
          </div>
          <div v-else-if="notifications.length === 0" class="py-12 text-center text-slate-400 text-xs">
            No notifications yet
          </div>
          <button
            v-else
            v-for="notif in notifications"
            :key="notif.id"
            @click="dismiss(notif)"
            :class="[
              'w-full flex items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-50',
              !notif.is_read ? 'bg-indigo-50/40' : ''
            ]"
          >
            <!-- Icon -->
            <span class="text-lg shrink-0 leading-none mt-0.5">{{ getIcon(notif.type) }}</span>
            <!-- Content -->
            <div class="flex-1 min-w-0">
              <p :class="['text-xs leading-snug', !notif.is_read ? 'font-bold text-slate-900' : 'font-medium text-slate-700']">
                {{ notif.title }}
              </p>
              <p v-if="notif.body" class="text-[10px] text-slate-400 mt-0.5 truncate">{{ notif.body }}</p>
              <p class="text-[9px] text-slate-300 mt-1 font-bold uppercase tracking-widest">{{ fmtTime(notif.created_at) }}</p>
            </div>
            <!-- Unread dot -->
            <span v-if="!notif.is_read" class="w-2 h-2 bg-indigo-500 rounded-full shrink-0 mt-1.5" />
          </button>
        </div>
      </div>
    </Transition>

    <!-- Backdrop -->
    <div v-if="open" class="fixed inset-0 z-40" @click="open = false" />
  </div>
</template>

<style scoped>
.drop-enter-active, .drop-leave-active { transition: all 0.15s ease; }
.drop-enter-from, .drop-leave-to { opacity: 0; transform: translateY(-6px) scale(0.97); }
.drop-enter-to, .drop-leave-from { opacity: 1; transform: translateY(0) scale(1); }
</style>
