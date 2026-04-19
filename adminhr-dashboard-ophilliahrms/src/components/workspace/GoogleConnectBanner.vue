<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  Calendar, 
  CheckCircle2, 
  RefreshCw, 
  AlertCircle, 
  Globe, 
  Link2, 
  Unlink2, 
  ShieldCheck,
  Zap,
  Activity,
  ShieldAlert
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useGoogleStore } from '@/stores/google.store'
import ConfirmDialog from '../ui/ConfirmDialog.vue'

const store = useGoogleStore()
const showDisconnectConfirm = ref(false)

onMounted(() => store.fetchStatus())

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

async function syncNow() {
  await store.syncCalendars()
}

async function handleDisconnect() {
  showDisconnectConfirm.value = false
  await store.disconnect()
}
</script>

<template>
  <div class="animate-in fade-in slide-in-from-top-4 duration-700">
    <!-- Integration: Inactive -->
    <div
      v-if="!store.isConnected"
      class="flex flex-col sm:flex-row items-center justify-between gap-6 px-8 py-6 bg-white/40 backdrop-blur-xl border border-white/20 rounded-[32px] shadow-2xl shadow-slate-200/40 relative overflow-hidden group"
    >
      <div class="absolute -left-12 -bottom-12 w-32 h-32 bg-blue-100/30 rounded-full blur-[60px] group-hover:bg-blue-100/50 transition-colors" />
      
      <div class="flex items-center gap-5 relative z-10">
        <div class="w-14 h-14 rounded-[22px] bg-blue-50/80 border border-blue-100 flex items-center justify-center flex-shrink-0 shadow-lg group-hover:scale-110 transition-transform">
          <Globe class="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h4 class="text-[13px] font-black text-slate-900 uppercase tracking-widest leading-none">External Node Authorization</h4>
          <p class="text-[11px] text-slate-500 font-medium mt-2 leading-relaxed max-w-[320px]">
            Initialize a secure synchronization bridge with Google Workspace to orchestrate events, tasks, and temporal metadata.
          </p>
        </div>
      </div>
      
      <Button
        @click="store.startOAuth()"
        class="flex-shrink-0 rounded-full px-8 h-11 bg-blue-600 text-white hover:bg-blue-700 shadow-xl shadow-blue-200 font-bold uppercase tracking-widest text-[11px] relative z-10"
      >
        <Link2 class="w-4 h-4 mr-2" />
        Authorize Node
      </Button>
    </div>

    <!-- Integration: Active -->
    <div v-else class="flex flex-col sm:flex-row items-center justify-between gap-6 px-8 py-6 bg-emerald-50/30 backdrop-blur-xl border border-emerald-100/50 rounded-[32px] shadow-2xl shadow-emerald-900/5 relative overflow-hidden group">
      <div class="absolute -left-12 -bottom-12 w-32 h-32 bg-emerald-100/20 rounded-full blur-[60px]" />
      
      <div class="flex items-center gap-5 relative z-10">
        <div class="w-14 h-14 rounded-[22px] bg-white border border-emerald-100 flex items-center justify-center flex-shrink-0 shadow-sm group-hover:scale-110 transition-transform">
          <ShieldCheck class="w-6 h-6 text-emerald-500" />
        </div>
        <div>
           <div class="flex items-center gap-2">
              <h4 class="text-[13px] font-black text-slate-900 uppercase tracking-widest leading-none">Authentication Synchronized</h4>
              <Badge variant="outline" class="h-5 px-2 bg-emerald-100/50 text-emerald-700 border-emerald-200 text-[8px] font-black uppercase tracking-widest">Active Link</Badge>
           </div>
           <p class="text-[11px] text-slate-500 font-bold mt-2">
             {{ store.integration?.google_email ?? 'Principal Identity Active' }}
             <span v-if="store.integration?.last_synced_at" class="mx-2 text-slate-300">|</span>
             <span v-if="store.integration?.last_synced_at" class="text-slate-400 font-medium">
               Last Sync: {{ formatTime(store.integration.last_synced_at) }}
             </span>
           </p>
        </div>
      </div>

      <div class="flex items-center gap-3 relative z-10">
        <Button
          variant="outline"
          size="sm"
          @click="syncNow"
          :disabled="store.syncing"
          class="h-10 rounded-full px-5 border-emerald-200 bg-white text-emerald-700 hover:bg-emerald-50 text-[10px] font-black uppercase tracking-widest shadow-sm"
        >
          <RefreshCw :class="['w-3.5 h-3.5 mr-2', store.syncing ? 'animate-spin text-emerald-500' : '']" />
          {{ store.syncing ? 'Synchronizing...' : 'Force Sync' }}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          @click="showDisconnectConfirm = true"
          class="h-10 rounded-full px-5 text-rose-500 hover:text-rose-600 hover:bg-rose-50 text-[10px] font-black uppercase tracking-widest"
        >
          <Unlink2 class="w-3.5 h-3.5 mr-2" />
          Sever Link
        </Button>
      </div>
    </div>

    <!-- Integration: Fault State -->
    <div v-if="store.integration?.status === 'revoked'" class="mt-4 flex items-center gap-3 bg-rose-50/50 backdrop-blur-sm border border-rose-100 px-6 py-4 rounded-[20px] animate-in slide-in-from-bottom-2">
      <div class="h-8 w-8 rounded-xl bg-white border border-rose-100 flex items-center justify-center shadow-sm">
        <ShieldAlert class="w-4 h-4 text-rose-500" />
      </div>
      <p class="text-[11px] font-bold text-rose-700 uppercase tracking-tight">
        Authorization Revoked: The synchronization bridge has encountered a terminal failure. Immediate recalibration required.
      </p>
    </div>

    <ConfirmDialog
      v-model:open="showDisconnectConfirm"
      title="Sever Synchronization Link"
      message="This action will terminate the real-time bridge with Google Workspace. Existing entries will persist as local cached data but synchronization protocol will cease."
      confirm-text="Confirm Disconnect"
      @confirm="handleDisconnect"
    />
  </div>
</template>
