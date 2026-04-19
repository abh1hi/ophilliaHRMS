<script setup lang="ts">
import { ref } from 'vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormSelect from '../ui/FormSelect.vue'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  X, 
  Plus, 
  Trash2, 
  Users, 
  UserPlus, 
  Shield, 
  ShieldCheck, 
  Eye, 
  Info,
  UserCheck,
  Zap,
  Network
} from 'lucide-vue-next'
import { useWorkspaceStore } from '@/stores/workspace.store'

interface Props {
  open: boolean
  workspaceId: string
}

const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'close'): void }>()

const store = useWorkspaceStore()
const newEmployeeId = ref('')
const newRole = ref<'admin' | 'member' | 'viewer'>('member')
const adding = ref(false)
const addError = ref<string | null>(null)

async function addMember() {
  if (!newEmployeeId.value.trim()) return
  adding.value = true
  addError.value = null
  try {
    await store.addWorkspaceMember(props.workspaceId, {
      employee_id: newEmployeeId.value.trim(),
      role: newRole.value,
    })
    newEmployeeId.value = ''
  } catch (e: unknown) {
    addError.value = e instanceof Error ? e.message : 'Failed to add member'
  } finally {
    adding.value = false
  }
}

async function changeRole(employeeId: string, role: string) {
  await store.updateWorkspaceMember(props.workspaceId, employeeId, {
    role: role as 'admin' | 'member' | 'viewer',
  })
}

async function removeMember(employeeId: string) {
  await store.removeWorkspaceMember(props.workspaceId, employeeId)
}

const roleOptions = [
  { value: 'admin', label: 'Systems Administrator' },
  { value: 'member', label: 'Operational Member' },
  { value: 'viewer', label: 'Passive Viewer' }
]

function getRoleIcon(role: string) {
  if (role === 'owner' || role === 'admin') return ShieldCheck
  if (role === 'member') return UserCheck
  return Eye
}
</script>

<template>
  <SlideDrawer 
    :open="open" 
    title="Resource Enrollment" 
    width="w-full max-w-md" 
    @close="emit('close')"
  >
    <div class="space-y-8 py-4">
      <div class="bg-indigo-50/30 p-4 rounded-2xl flex items-start gap-3 border border-indigo-100/50 mb-2">
         <Info class="w-4 h-4 text-indigo-500 mt-0.5" />
         <p class="text-[11px] text-indigo-700 font-medium leading-relaxed">
           Enroll secondary resources into this environmental hub. Roles determine the synchronization depth and operational permissions for each personnel node.
         </p>
      </div>

      <!-- Add member section -->
      <div class="space-y-4">
        <div class="flex items-center gap-2 mb-2">
           <UserPlus class="w-4 h-4 text-slate-400" />
           <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Initialize Enrollment</span>
        </div>
        
        <div class="p-6 bg-slate-50/50 rounded-[32px] border border-white/10 space-y-4 relative overflow-hidden">
           <Network class="absolute -right-4 -top-4 w-16 h-16 text-slate-900/5 -rotate-12" />
           <div class="space-y-4">
              <FormInput label="Resource Identity" v-model="newEmployeeId" placeholder="Hardware ID (e.g. EMP-001)..." />
              <FormSelect label="Hierarchy Calibration" v-model="newRole" :options="roleOptions" />
              <Button 
                @click="addMember" 
                :disabled="!newEmployeeId.trim() || adding" 
                class="w-full rounded-2xl h-12 bg-slate-900 text-white font-bold uppercase tracking-widest text-[11px] hover:bg-slate-800 shadow-xl shadow-slate-200"
              >
                {{ adding ? 'Synchronizing...' : 'Enroll Resource' }}
              </Button>
           </div>
           <p v-if="addError" class="text-[10px] font-bold text-destructive uppercase tracking-tight text-center">{{ addError }}</p>
        </div>
      </div>

      <!-- Member list -->
      <div class="space-y-4">
        <div class="flex items-center gap-2 mb-2">
           <Users class="w-4 h-4 text-slate-400" />
           <span class="text-[10px] font-black uppercase tracking-widest text-slate-900">Active Node Matrix</span>
        </div>

        <div v-if="store.members.length" class="space-y-3">
          <div
            v-for="member in store.members"
            :key="member.id"
            class="group flex items-center justify-between p-4 bg-white hover:bg-slate-50 border border-slate-100 rounded-[22px] transition-all"
          >
            <div class="flex items-center gap-3">
               <div class="h-9 w-9 rounded-xl bg-slate-100 flex items-center justify-center shrink-0 border border-white/50">
                  <component :is="getRoleIcon(member.role)" class="w-4 h-4 text-slate-400" />
               </div>
               <div>
                  <p class="text-[11px] font-bold text-slate-900 tracking-tight">{{ member.employee_id }}</p>
                  <p class="text-[9px] text-slate-400 font-black uppercase tracking-widest">{{ member.role }}</p>
               </div>
            </div>

            <div class="flex items-center gap-2">
               <select
                 :value="member.role"
                 @change="changeRole(member.employee_id, ($event.target as HTMLSelectElement).value)"
                 :disabled="member.role === 'owner'"
                 class="text-[10px] font-bold uppercase tracking-tight bg-slate-100 border-none rounded-lg px-2 py-1 outline-none disabled:opacity-30"
               >
                 <option value="owner" disabled>Owner</option>
                 <option value="admin">Admin</option>
                 <option value="member">Member</option>
                 <option value="viewer">Viewer</option>
               </select>
               <Button
                 v-if="member.role !== 'owner'"
                 variant="ghost"
                 size="icon"
                 @click="removeMember(member.employee_id)"
                 class="h-8 w-8 rounded-xl opacity-0 group-hover:opacity-100 text-slate-300 hover:text-destructive transition-all"
               >
                 <Trash2 class="w-4 h-4" />
               </Button>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-10 border border-dashed border-slate-200 rounded-[28px] bg-slate-50/30">
           <Users class="w-8 h-8 text-slate-300 mx-auto mb-3" />
           <p class="text-[11px] text-slate-400 font-bold uppercase tracking-widest italic">Hub Matrix is currently unpopulated</p>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-end">
        <Button variant="outline" @click="emit('close')" class="rounded-full px-8 h-10 font-bold uppercase tracking-widest text-[11px]">Terminate Session</Button>
      </div>
    </template>
  </SlideDrawer>
</template>
