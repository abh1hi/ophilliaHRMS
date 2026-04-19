<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { Button } from '../ui/button'
import { Checkbox } from '../ui/checkbox'
import { Label } from '../ui/label'
import { Pencil, Plus, Trash2 } from 'lucide-vue-next'
import { listLeavePolicies, createLeavePolicy, updateLeavePolicy } from '../../services/leave-policy.service'
import type { LeavePolicy, LeavePolicyItem } from '../../services/leave-policy.service'

const rows = ref<LeavePolicy[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const selected = ref<LeavePolicy | null>(null)
const form = ref<Partial<LeavePolicy> & { items: Partial<LeavePolicyItem>[] }>({ items: [] })
const saving = ref(false)
const errorMsg = ref('')

const columns = [
  { key: 'name', label: 'Policy Name' },
  { key: 'description', label: 'Description' },
  { key: 'is_active', label: 'Active' },
]

async function load() {
  loading.value = true
  try { rows.value = await listLeavePolicies(true) } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() {
  selected.value = null
  form.value = { is_active: 1, items: [{ leave_type_id: '', annual_allocation: 0 }] }
  errorMsg.value = ''; drawerOpen.value = true
}
function openEdit(row: LeavePolicy) {
  selected.value = row
  form.value = { ...row, items: row.items.map(i => ({ ...i })) }
  errorMsg.value = ''; drawerOpen.value = true
}

function addItem() { form.value.items.push({ leave_type_id: '', annual_allocation: 0 }) }
function removeItem(i: number) { form.value.items.splice(i, 1) }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    const payload = { ...form.value }
    if (selected.value) await updateLeavePolicy(selected.value.id, payload)
    else await createLeavePolicy(payload)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
</script>

<template>
  <div class="space-y-8">
    <PageHeader 
      title="Leave Policies" 
      subtitle="Define leave entitlements per leave type" 
      action-label="New Policy" 
      @action="openCreate" 
    />
    
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No leave policies yet.">
      <template #cell-is_active="{ value }">
        <span 
          :class="value ? 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50'" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
        >
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>
      <template #actions="{ row }">
        <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-8 w-8 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900">
          <Pencil class="w-4 h-4" />
        </Button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Policy' : 'Create Leave Policy'" width="w-full max-w-xl" @close="drawerOpen = false">
      <div class="space-y-6">
        <FormInput label="Policy Name" :modelValue="form.name" @update:modelValue="form.name = $event" placeholder="e.g. Standard Corporate Policy" required />
        <FormTextarea label="Description" :modelValue="form.description" @update:modelValue="form.description = $event" placeholder="Internal notes about who this policy applies to..." />
        
        <div class="flex items-center space-x-2 bg-muted/30 p-4 rounded-xl border border-dashed">
          <Checkbox id="lp-active" :checked="!!form.is_active" @update:checked="form.is_active = $event ? 1 : 0" />
          <Label for="lp-active" class="text-xs font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">Active Policy</Label>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h4 class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Policy Entitlements</h4>
            <Button variant="ghost" size="sm" @click="addItem" class="h-7 text-[10px] font-bold uppercase gap-1 hover:bg-slate-100">
              <Plus class="w-3 h-3" /> Add Leave Type
            </Button>
          </div>

          <div class="space-y-3">
            <div v-for="(item, i) in form.items" :key="i" class="relative g-glass-card p-4 rounded-xl border border-slate-200/60 bg-white/50 animate-in fade-in slide-in-from-top-1">
              <div class="grid grid-cols-12 gap-4 items-end">
                <div class="col-span-12 sm:col-span-7">
                  <FormInput label="Leave Type ID" :modelValue="item.leave_type_id" @update:modelValue="item.leave_type_id = $event" placeholder="e.g. SL, CL, PL" />
                </div>
                <div class="col-span-10 sm:col-span-4">
                  <FormInput label="Annual Allocation" type="number" :modelValue="String(item.annual_allocation ?? 0)" @update:modelValue="item.annual_allocation = Number($event)" />
                </div>
                <div class="col-span-2 sm:col-span-1 flex justify-end">
                  <Button variant="ghost" size="icon" @click="removeItem(i)" class="h-9 w-9 text-slate-400 hover:text-destructive hover:bg-destructive/10 rounded-lg">
                    <Trash2 class="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving...' : 'Save Policy' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
