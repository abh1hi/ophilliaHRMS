<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  RefreshCw, 
  StickyNote, 
  AlertCircle,
  Zap,
  ShieldAlert,
  ArrowRight,
  Monitor,
  Search,
  Layers,
  Sparkles,
  Info
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useGoogleStore } from '@/stores/google.store'
import { apiFetchData } from '@/services/http'

interface KeepNote {
  id: string
  title?: string
  body: string
  color?: string
  updated_at: string
}

const store = useGoogleStore()
const notes = ref<KeepNote[]>([])
const loading = ref(false)
const notWorkspaceAccount = ref(false)

onMounted(async () => {
  await store.fetchStatus()
  if (store.isConnected) await refresh()
})

async function refresh() {
  loading.value = true
  notWorkspaceAccount.value = false
  try {
    const result = await apiFetchData<KeepNote[]>('/calendar/google/notes')
    if (result) notes.value = result
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : ''
    if (msg.includes('workspace') || msg.includes('403')) {
      notWorkspaceAccount.value = true
    }
  } finally {
    loading.value = false
  }
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="h-full flex flex-col space-y-6">
    <div class="flex items-center justify-between">
      <div class="space-y-1">
        <h3 class="text-lg font-black text-slate-900 uppercase tracking-tight flex items-center gap-2">
          <Layers class="w-5 h-5 text-slate-400" />
          Intelligence Matrix
        </h3>
        <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest leading-none">External Memory Synchronization</p>
      </div>
      
      <Button
        v-if="store.isConnected"
        variant="outline"
        @click="refresh"
        :disabled="loading"
        class="h-9 px-4 rounded-full border-slate-200 text-[10px] font-black uppercase tracking-widest hover:border-indigo-200 hover:text-indigo-600 transition-all"
      >
        <RefreshCw :class="['w-3.5 h-3.5 mr-2', loading ? 'animate-spin' : '']" />
        Sync Matrix
      </Button>
    </div>

    <!-- Interface Protocols: Connection Matrix -->
    <div v-if="!store.isConnected" class="flex-1 flex flex-col items-center justify-center text-center p-8 rounded-[40px] bg-slate-50/50 border border-dashed border-slate-200 group">
      <div class="relative mb-6">
        <div class="absolute inset-0 bg-indigo-100 rounded-[28px] blur-2xl opacity-20 group-hover:opacity-40 transition-opacity" />
        <div class="relative w-16 h-16 rounded-[28px] bg-white border border-slate-100 shadow-sm flex items-center justify-center group-hover:scale-110 transition-transform">
          <Monitor class="w-8 h-8 text-slate-300" />
        </div>
      </div>
      <div class="space-y-4">
        <div>
          <p class="text-[12px] font-black text-slate-900 uppercase tracking-widest">Protocol Offline</p>
          <p class="text-[11px] text-slate-400 font-medium mt-2 max-w-xs leading-relaxed">
            Initialize Google OAuth sequence to synchronize external memory nodes with the local matrix.
          </p>
        </div>
        <Button
          @click="store.startOAuth()"
          class="h-10 rounded-full px-6 bg-slate-900 text-white hover:bg-black shadow-lg shadow-slate-100 text-[10px] font-bold uppercase tracking-widest"
        >
          Initialize Sync Protocol
          <ArrowRight class="w-3.5 h-3.5 ml-2" />
        </Button>
      </div>
    </div>

    <!-- Constraint Notice: Workspace Isolation -->
    <div v-else-if="notWorkspaceAccount" class="flex-1 flex flex-col items-center justify-center text-center p-8 rounded-[40px] bg-amber-50/30 border border-amber-100 group">
      <div class="relative mb-6">
        <div class="absolute inset-0 bg-amber-200 rounded-[28px] blur-2xl opacity-20" />
        <div class="relative w-16 h-16 rounded-[28px] bg-white border border-amber-100 shadow-sm flex items-center justify-center">
          <ShieldAlert class="w-8 h-8 text-amber-500" />
        </div>
      </div>
      <div class="space-y-4">
        <div>
          <p class="text-[12px] font-black text-slate-900 uppercase tracking-widest">Workspace Invariant Detected</p>
          <p class="text-[11px] text-amber-900/60 font-medium mt-2 max-w-xs leading-relaxed">
             Intelligence ingestion protocol requires an Enterprise-tier Google Workspace manifest. Personal domains are restricted by API security layers.
          </p>
        </div>
      </div>
    </div>

    <!-- Synchronized Memory Nodes -->
    <div v-else class="flex-1 overflow-y-auto no-scrollbar pb-4">
      <div v-if="loading" class="grid grid-cols-2 gap-4">
        <div v-for="i in 6" :key="i" class="h-32 bg-slate-100/50 animate-pulse rounded-[24px] border border-slate-100" />
      </div>
      
      <div v-else-if="notes.length" class="grid grid-cols-2 gap-4">
        <div
          v-for="note in notes"
          :key="note.id"
          class="relative overflow-hidden rounded-[24px] border border-white/40 p-4 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all group backdrop-blur-sm"
          :style="{ 
            backgroundColor: `${note.color ?? '#fef9c3'}22`,
            borderColor: `${note.color ?? '#fef9c3'}66`
          }"
        >
          <div class="absolute -right-4 -top-4 w-12 h-12 rounded-full blur-xl transition-all" :style="{ backgroundColor: note.color ?? '#fef9c3' }" />
          
          <div class="relative z-10">
            <p v-if="note.title" class="text-[12px] font-black text-slate-900 mb-2 truncate uppercase tracking-tight">{{ note.title }}</p>
            <p class="text-[11px] text-slate-600 font-medium line-clamp-5 leading-relaxed bg-white/40 p-2 rounded-xl border border-white/20 shadow-inner">
              {{ note.body }}
            </p>
            <div class="mt-3 flex items-center justify-between">
              <span class="text-[9px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1.5">
                <Clock class="w-3 h-3" /> {{ formatTime(note.updated_at) }}
              </span>
              <Badge variant="outline" class="h-4 px-1.5 text-[7px] border-black/5 bg-white/20 backdrop-blur-md uppercase tracking-tighter">Memory Node</Badge>
            </div>
          </div>
        </div>
      </div>

      <!-- Ingestion Void -->
      <div v-else class="flex flex-col items-center justify-center py-20 text-center rounded-[40px] bg-slate-50/30 border border-dashed border-slate-200">
        <div class="w-12 h-12 rounded-full bg-white border border-slate-100 shadow-sm flex items-center justify-center mb-4">
          <Sparkles class="w-5 h-5 text-slate-200" />
        </div>
        <p class="text-[11px] font-black text-slate-300 uppercase tracking-widest">Memory Matrix Empty</p>
        <p class="text-[9px] text-slate-400 font-medium mt-1 uppercase tracking-tight">No intelligence manifests discovered</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
