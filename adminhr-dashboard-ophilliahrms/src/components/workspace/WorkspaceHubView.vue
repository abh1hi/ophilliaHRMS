<template>
  <div class="space-y-6">
    <!-- Google banner -->
    <GoogleConnectBanner />

    <!-- Workspace selector / create -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h3 class="text-base font-semibold text-slate-800">Workspaces</h3>
        <span class="text-xs text-slate-400">{{ store.workspaces.length }} total</span>
      </div>
      <button
        @click="showCreate = true"
        class="flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 text-white text-sm rounded-lg hover:bg-slate-700"
      >
        <PlusIcon class="w-4 h-4" />
        New Workspace
      </button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="i in 3" :key="i" class="h-28 bg-slate-100 animate-pulse rounded-2xl" />
    </div>

    <!-- Workspace cards -->
    <div v-else-if="store.workspaces.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="ws in store.workspaces"
        :key="ws.id"
        class="group bg-white border border-slate-200 rounded-2xl p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition-all cursor-pointer"
        @click="selectWorkspace(ws)"
      >
        <div class="flex items-start justify-between mb-3">
          <div
            class="w-10 h-10 rounded-xl flex items-center justify-center text-white text-sm font-bold"
            :style="{ backgroundColor: ws.color ?? '#1e293b' }"
          >
            {{ ws.name.charAt(0).toUpperCase() }}
          </div>
          <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              @click.stop="editTarget = ws; showEdit = true"
              class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400"
            >
              <PencilIcon class="w-3.5 h-3.5" />
            </button>
            <button
              @click.stop="openMembers(ws)"
              class="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400"
            >
              <UsersIcon class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        <p class="text-sm font-semibold text-slate-800 truncate">{{ ws.name }}</p>
        <p v-if="ws.description" class="text-xs text-slate-500 truncate mt-0.5">{{ ws.description }}</p>
        <div class="flex items-center gap-2 mt-3">
          <span class="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full capitalize">{{ ws.workspace_type }}</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="text-center py-16">
      <LayoutGridIcon class="w-12 h-12 text-slate-200 mx-auto mb-3" />
      <p class="text-sm font-medium text-slate-600">No workspaces yet</p>
      <p class="text-xs text-slate-400 mt-1">Create a workspace to collaborate with your team</p>
    </div>

    <!-- Create / Edit workspace panel -->
    <WorkspacePanel :open="showCreate || showEdit" :workspace="showEdit ? editTarget : null" @close="showCreate = false; showEdit = false" @saved="store.fetchWorkspaces()" />

    <!-- Member panel -->
    <WorkspaceMemberPanel
      v-if="memberWorkspaceId"
      :open="showMembers"
      :workspace-id="memberWorkspaceId"
      @close="showMembers = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { PlusIcon, PencilIcon, UsersIcon, LayoutGridIcon } from 'lucide-vue-next'
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
