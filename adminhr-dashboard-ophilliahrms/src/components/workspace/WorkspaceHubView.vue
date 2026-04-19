<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { 
  Plus, 
  Pencil, 
  Users, 
  LayoutGrid, 
  Box, 
  Layers, 
  Settings, 
  Archive, 
  Info,
  ChevronRight,
  Monitor,
  Zap
} from 'lucide-vue-next'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useWorkspaceStore } from '@/stores/workspace.store'
import WorkspacePanel from './WorkspacePanel.vue'
import WorkspaceMemberPanel from './WorkspaceMemberPanel.vue'
import GoogleConnectBanner from './GoogleConnectBanner.vue'
import type { Workspace } from '@/services/calendar-workspace.service'

const store = useWorkspaceStore()
const showCreate = ref(false)
const showEdit = ref(false)
const showMembers = ref(false)
const editTarget = ref<Workspace | null>(null)
const memberWorkspaceId = ref<string | null>(null)

onMounted(() => store.fetchWorkspaces())

function selectWorkspace(ws: Workspace) {
  store.selectWorkspace(ws.id)
}

function openMembers(ws: Workspace) {
  memberWorkspaceId.value = ws.id
  store.fetchMembers(ws.id)
  showMembers.value = true
}
</script>

<template>
  <div class="space-y-10 animate-in fade-in duration-700">
    <!-- Integration Layer -->
    <div class="p-6 bg-white/40 backdrop-blur-xl rounded-[32px] border border-white/20 shadow-xl shadow-slate-200/40 overflow-hidden relative group">
       <div class="absolute -right-12 -top-12 w-32 h-32 bg-indigo-50/50 rounded-full blur-[60px] group-hover:bg-indigo-100/50 transition-colors" />
       <GoogleConnectBanner />
    </div>

    <!-- Orchestration Header -->
    <div class="flex items-center justify-between px-1">
      <div class="flex items-center gap-4">
         <div class="h-12 w-12 rounded-[22px] bg-slate-900 flex items-center justify-center shadow-xl shadow-slate-200">
            <Layers class="w-5 h-5 text-white" />
         </div>
         <div>
            <h3 class="text-lg font-black text-slate-900 uppercase tracking-widest leading-none">Environmental Hubs</h3>
            <p class="text-[11px] text-slate-400 font-bold uppercase tracking-tight mt-1">{{ store.workspaces.length }} Managed Node{{ store.workspaces.length !== 1 ? 's' : '' }}</p>
         </div>
      </div>
      <Button
        @click="showCreate = true"
        class="h-11 rounded-full px-6 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 font-bold uppercase tracking-widest text-[11px]"
      >
        <Plus class="w-4 h-4 mr-2" />
        Initialize Hub
      </Button>
    </div>

    <!-- Synchronized Grid -->
    <div v-if="store.loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 px-1">
      <div v-for="i in 3" :key="i" class="h-44 bg-slate-100/50 backdrop-blur-sm border border-slate-100 animate-pulse rounded-[32px]" />
    </div>

    <div v-else-if="store.workspaces.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 px-1">
      <div
        v-for="ws in store.workspaces"
        :key="ws.id"
        class="group relative bg-white/40 backdrop-blur-xl border border-white/20 rounded-[32px] p-6 shadow-xl shadow-slate-200/30 hover:shadow-2xl hover:shadow-slate-200/50 hover:border-white/40 hover:-translate-y-1 transition-all duration-500 cursor-pointer overflow-hidden"
        @click="selectWorkspace(ws)"
      >
        <!-- Card Decoration -->
        <div 
          class="absolute -right-8 -top-8 w-24 h-24 rounded-full opacity-10 blur-2xl group-hover:opacity-20 transition-opacity"
          :style="{ backgroundColor: ws.color ?? '#1e293b' }"
        />
        
        <div class="flex items-start justify-between mb-6">
          <div
            class="w-12 h-12 rounded-[18px] flex items-center justify-center text-white text-base font-black shadow-lg transition-transform group-hover:scale-110"
            :style="{ backgroundColor: ws.color ?? '#1e293b', boxShadow: `0 8px 16px ${(ws.color ?? '#1e293b') + '40'}` }"
          >
            {{ ws.name.charAt(0).toUpperCase() }}
          </div>
          <div class="flex gap-1.5 opacity-0 group-hover:opacity-100 translate-x-4 group-hover:translate-x-0 transition-all duration-300">
            <Button
              variant="ghost"
              size="icon"
              @click.stop="editTarget = ws; showEdit = true"
              class="h-8 w-8 rounded-xl bg-white/60 hover:bg-white text-slate-400 hover:text-slate-900 border border-white/20"
            >
              <Pencil class="w-3.5 h-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              @click.stop="openMembers(ws)"
              class="h-8 w-8 rounded-xl bg-white/60 hover:bg-white text-slate-400 hover:text-slate-900 border border-white/20"
            >
              <Users class="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>

        <div class="space-y-1 mb-6">
          <p class="text-[13px] font-black text-slate-900 uppercase tracking-tight truncate">{{ ws.name }}</p>
          <p v-if="ws.description" class="text-[11px] text-slate-400 font-medium line-clamp-2 leading-relaxed h-8">{{ ws.description }}</p>
          <p v-else class="text-[11px] text-slate-300 font-medium italic">No operational brief provided</p>
        </div>

        <div class="flex items-center justify-between">
           <Badge variant="outline" class="h-6 rounded-full px-3 bg-slate-50/50 text-[9px] font-black uppercase tracking-widest text-slate-500 border-slate-100 group-hover:border-slate-200 group-hover:bg-white transition-colors">
              {{ ws.workspace_type }}
           </Badge>
           <ChevronRight class="w-3.5 h-3.5 text-slate-300 group-hover:text-slate-900 group-hover:translate-x-1 transition-all" />
        </div>
      </div>
    </div>

    <!-- Null State Architecture -->
    <div v-else class="flex flex-col items-center justify-center py-20 bg-slate-50/30 backdrop-blur-sm rounded-[44px] border border-dashed border-slate-200">
      <div class="h-20 w-20 rounded-[30px] bg-white shadow-xl shadow-slate-200/50 flex items-center justify-center mb-6">
         <Box class="w-10 h-10 text-slate-200" />
      </div>
      <p class="text-sm font-black text-slate-900 uppercase tracking-widest">Architecture Inactive</p>
      <p class="text-[11px] text-slate-400 font-bold uppercase tracking-tight mt-2 max-w-[240px] text-center">No synchronized hubs identified. Initialize a workspace to commence environmental orchestration.</p>
      <Button
        variant="outline"
        @click="showCreate = true"
        class="mt-8 rounded-full h-10 px-8 border-slate-200 text-slate-900 font-black uppercase tracking-widest text-[10px] hover:bg-white"
      >
        Initialize Hub Sequence
      </Button>
    </div>

    <!-- Interaction Interfaces -->
    <WorkspacePanel 
      :open="showCreate || showEdit" 
      :workspace="showEdit ? editTarget : null" 
      @close="showCreate = false; showEdit = false" 
      @saved="store.fetchWorkspaces()" 
    />

    <WorkspaceMemberPanel
      v-if="memberWorkspaceId"
      :open="showMembers"
      :workspace-id="memberWorkspaceId"
      @close="showMembers = false"
    />
  </div>
</template>
