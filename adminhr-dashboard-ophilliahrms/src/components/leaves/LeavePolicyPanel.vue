<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import FormTextarea from '../ui/FormTextarea.vue'
import { PencilIcon, PlusIcon, Trash2Icon } from 'lucide-vue-next'
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
    if (selected.value) await updateLeavePolicy(selected.value.id, form.value)
    else await createLeavePolicy(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader title="Leave Policies" subtitle="Define leave entitlements per leave type" action-label="+ New Policy" @action="openCreate" />
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No leave policies yet.">
      <template #cell-is_active="{ value }">
        <span :class="value ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ value ? 'Active' : 'Inactive' }}</span>
      </template>
      <template #actions="{ row }">
        <button @click="openEdit(row)" class="p-2 rounded-[10px] hover:bg-slate-100 text-slate-500 hover:text-slate-800 transition-colors"><PencilIcon class="w-4 h-4" /></button>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Policy' : 'New Leave Policy'" width="w-full max-w-xl" @close="drawerOpen = false">
      <div class="space-y-5">
        <FormInput label="Policy Name" :modelValue="form.name" @update:modelValue="form.name = $event" required />
        <FormTextarea label="Description" :modelValue="form.description" @update:modelValue="form.description = $event" />
        <div class="flex items-center gap-3">
          <input type="checkbox" id="lp-active" :checked="!!form.is_active" @change="form.is_active = ($event.target as HTMLInputElement).checked ? 1 : 0" class="w-4 h-4 rounded" />
          <label for="lp-active" class="text-sm font-medium text-slate-700">Active</label>
        </div>

        <div class="space-y-3">
          <label class="block text-sm font-semibold text-slate-700">Policy Items (Leave Type → Annual Days)</label>
          <div v-for="(item, i) in form.items" :key="i" class="flex gap-2 items-end">
            <FormInput label="Leave Type ID" :modelValue="item.leave_type_id" @update:modelValue="item.leave_type_id = $event" class="flex-1" />
            <FormInput label="Days/Year" type="number" :modelValue="String(item.annual_allocation ?? 0)" @update:modelValue="item.annual_allocation = Number($event)" class="w-28" />
            <button @click="removeItem(i)" class="mb-1 p-2 rounded-[10px] hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors"><Trash2Icon class="w-4 h-4" /></button>
          </div>
          <button @click="addItem" class="text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1"><PlusIcon class="w-4 h-4" /> Add Leave Type</button>
        </div>
      </div>
      <template #footer>
        <div class="flex items-center justify-between">
          <p v-if="errorMsg" class="text-sm text-rose-600">{{ errorMsg }}</p><div v-else></div>
          <div class="flex space-x-3">
            <button @click="drawerOpen = false" class="px-5 py-2.5 border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-full font-medium text-sm transition-colors">Cancel</button>
            <button @click="save" :disabled="saving" class="px-6 py-2.5 bg-slate-900 text-white rounded-full font-medium text-sm hover:bg-slate-800 transition-all disabled:opacity-60">{{ saving ? 'Saving...' : 'Save' }}</button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
