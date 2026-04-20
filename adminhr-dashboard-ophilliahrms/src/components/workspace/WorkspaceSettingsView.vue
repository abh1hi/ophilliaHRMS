<template>
  <div class="max-w-3xl space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
    <!-- Environmental Configuration -->
    <div class="bg-white/40 backdrop-blur-xl border border-white/20 rounded-[32px] p-8 space-y-8 shadow-xl shadow-slate-200/50 relative overflow-hidden group">
      <div class="absolute -right-12 -top-12 w-40 h-40 bg-indigo-50/50 rounded-full blur-[80px] group-hover:bg-indigo-100/50 transition-colors duration-700" />
      
      <div class="flex items-center gap-3">
         <div class="h-10 w-10 rounded-2xl bg-slate-900 flex items-center justify-center shadow-lg shadow-slate-200">
            <Settings class="w-5 h-5 text-white" />
         </div>
         <div>
            <h3 class="text-base font-black text-slate-900 uppercase tracking-widest">Workspace Management</h3>
            <p class="text-[11px] text-slate-500 font-bold uppercase tracking-tight">Manage workspaces and settings</p>
         </div>
      </div>

      <div class="space-y-6">
        <div class="flex flex-col gap-2">
           <label class="text-[10px] font-black uppercase tracking-widest text-slate-400 ml-1">Select Workspace</label>
           <div class="flex gap-3">
              <FormSelect 
                v-model="selectedId" 
                :options="workspaceOptions" 
                placeholder="Initialize hub management..."
                class="flex-1"
              />
              <div v-if="selectedId" class="flex gap-2 animate-in fade-in zoom-in-95">
                <Button variant="outline" @click="editWorkspace" class="rounded-2xl h-12 px-5 font-bold uppercase tracking-widest text-[11px] border-slate-200 hover:bg-slate-50">
                   <Edit class="w-4 h-4 mr-2" />
                   Edit
                </Button>
                <Button variant="ghost" @click="showDeleteConfirm = true" class="rounded-2xl h-12 px-5 font-bold uppercase tracking-widest text-[11px] text-destructive hover:bg-destructive/5">
                   <Trash2 class="w-4 h-4 mr-2" />
                   Delete
                </Button>
              </div>
           </div>
        </div>

        <div v-if="store.workspaces.length === 0" class="flex flex-col items-center py-10 border border-dashed border-slate-200 rounded-[24px] bg-slate-50/30">
           <Layout class="w-8 h-8 text-slate-300 mb-3" />
           <p class="text-[11px] text-slate-400 font-bold uppercase tracking-widest">No workspaces yet</p>
        </div>
      </div>
    </div>

    <!-- External Synchronization Protocol -->
    <div class="bg-white/40 backdrop-blur-xl border border-white/20 rounded-[32px] p-8 space-y-8 shadow-xl shadow-slate-200/50 relative overflow-hidden group">
      <div class="absolute -left-12 -bottom-12 w-40 h-40 bg-blue-50/50 rounded-full blur-[80px] group-hover:bg-blue-100/50 transition-colors duration-700" />
      
      <div class="flex items-center gap-3">
         <div class="h-10 w-10 rounded-2xl bg-blue-600 flex items-center justify-center shadow-lg shadow-blue-200">
            <Globe class="w-5 h-5 text-white" />
         </div>
         <div>
            <h3 class="text-base font-black text-slate-900 uppercase tracking-widest text-blue-900">Google Calendar Integration</h3>
            <p class="text-[11px] text-slate-500 font-bold uppercase tracking-tight">Connect and sync your Google Calendar</p>
         </div>
      </div>

      <div class="space-y-6">
        <div class="p-6 bg-slate-50/50 rounded-[28px] border border-white/10">
           <GoogleConnectBanner />
        </div>

        <!-- Connected calendars -->
        <div v-if="googleStore.isConnected" class="space-y-6 animate-in fade-in slide-in-from-top-2">
          <div class="flex items-center justify-between border-b border-slate-100 pb-4">
            <div class="flex items-center gap-2">
               <Shield class="w-4 h-4 text-blue-500" />
               <p class="text-[11px] font-black uppercase tracking-widest text-slate-900">Connected Calendars</p>
            </div>
            <Button variant="ghost" size="sm" @click="fetchGoogleCals" class="h-8 rounded-full text-[10px] font-bold uppercase tracking-widest text-blue-600 hover:bg-blue-50">
               Manage Calendars
            </Button>
          </div>

          <div v-if="googleStore.connectedCalendars.length" class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div
              v-for="cal in googleStore.connectedCalendars"
              :key="cal.id"
              class="flex items-center gap-3 px-4 py-3 bg-white border border-slate-100 rounded-2xl shadow-sm hover:border-blue-200 transition-all group"
            >
              <div class="h-2 w-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)] group-hover:scale-125 transition-transform" />
              <span class="text-[11px] font-bold text-slate-700 tracking-tight">{{ cal.summary }}</span>
              <Badge v-if="cal.primary" variant="secondary" class="ml-auto rounded-full px-2 py-0 bg-blue-50 text-blue-600 text-[9px] font-black uppercase tracking-tighter">Primary</Badge>
            </div>
          </div>
          <div v-else class="text-center py-6 border border-dashed border-slate-100 rounded-2xl">
             <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest italic">No calendars connected yet</p>
          </div>

          <!-- Google calendar selector -->
          <div v-if="showCalSelector" class="p-6 bg-blue-50/30 border border-blue-100/50 rounded-[28px] space-y-4 animate-in zoom-in-95">
            <p class="text-[10px] font-black uppercase tracking-widest text-blue-600 mb-2">Select Calendars to Connect</p>
            <div class="grid grid-cols-1 gap-2">
              <div
                v-for="cal in googleStore.availableCalendars"
                :key="cal.id"
                class="flex items-center gap-3 p-3 bg-white/60 hover:bg-white rounded-xl transition-colors cursor-pointer"
                @click="toggleCalSelection(cal.id)"
              >
                <div class="h-5 w-5 rounded-md border border-slate-200 flex items-center justify-center transition-all" :class="selectedGoogleCals.includes(cal.id) ? 'bg-blue-600 border-blue-600' : 'bg-white'">
                   <Check v-if="selectedGoogleCals.includes(cal.id)" class="w-3 h-3 text-white" />
                </div>
                <label :for="cal.id" class="text-[11px] font-bold text-slate-700 cursor-pointer">{{ cal.summary }}</label>
              </div>
            </div>
            <div class="flex gap-3 pt-2">
              <Button @click="saveGoogleCals" class="rounded-full px-8 h-10 bg-blue-600 text-white font-bold uppercase tracking-widest text-[10px] hover:bg-blue-700 shadow-lg shadow-blue-100">
                 Save
              </Button>
              <Button variant="ghost" @click="showCalSelector = false" class="rounded-full px-6 h-10 font-bold uppercase tracking-widest text-[10px]">Cancel</Button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit panel -->
    <WorkspacePanel
      :open="showEdit"
      :workspace="editTarget"
      @close="showEdit = false"
      @saved="store.fetchWorkspaces()"
    />

    <ConfirmDialog
      :open="showDeleteConfirm"
      title="Delete Workspace?"
      message="Are you sure you want to delete this workspace? This action cannot be undone."
      @confirm="handleDelete"
      @cancel="showDeleteConfirm = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace.store'
import { useGoogleStore } from '@/stores/google.store'
import WorkspacePanel from './WorkspacePanel.vue'
import GoogleConnectBanner from './GoogleConnectBanner.vue'
import FormSelect from '../ui/FormSelect.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Settings, 
  Globe, 
  Shield, 
  Edit, 
  Trash2, 
  Layout, 
  Check,
  ChevronRight,
  Info
} from 'lucide-vue-next'
import type { Workspace } from '@/services/calendar-workspace.service'

const store = useWorkspaceStore()
const googleStore = useGoogleStore()
const selectedId = ref('')
const showEdit = ref(false)
const editTarget = ref<Workspace | null>(null)
const showCalSelector = ref(false)
const selectedGoogleCals = ref<string[]>([])
const showDeleteConfirm = ref(false)

const workspaceOptions = computed(() => 
  store.workspaces.map(ws => ({ value: ws.id, label: ws.name }))
)

onMounted(() => {
  store.fetchWorkspaces()
  googleStore.fetchStatus()
})

function editWorkspace() {
  editTarget.value = store.workspaces.find(w => w.id === selectedId.value) ?? null
  showEdit.value = true
}

async function handleDelete() {
  if (!selectedId.value) return
  await store.remove(selectedId.value)
  selectedId.value = ''
  showDeleteConfirm.value = false
}

async function fetchGoogleCals() {
  showCalSelector.value = true
  await googleStore.fetchGoogleCalendars()
  selectedGoogleCals.value = googleStore.connectedCalendars.map(c => c.id)
}

function toggleCalSelection(id: string) {
  const idx = selectedGoogleCals.value.indexOf(id)
  if (idx > -1) selectedGoogleCals.value.splice(idx, 1)
  else selectedGoogleCals.value.push(id)
}

async function saveGoogleCals() {
  await googleStore.connectSelectedCalendars(selectedGoogleCals.value)
  showCalSelector.value = false
}
</script>
