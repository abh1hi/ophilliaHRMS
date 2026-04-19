<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import { Button } from '../ui/button'
import { Checkbox } from '../ui/checkbox'
import { Label } from '../ui/label'
import { Pencil, Plus, Trash2 } from 'lucide-vue-next'
import { listLeaveBlockLists, createLeaveBlockList, updateLeaveBlockList } from '../../services/leave-block-list.service'
import type { LeaveBlockList, LeaveBlockListDate } from '../../services/leave-block-list.service'

const rows = ref<LeaveBlockList[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const selected = ref<LeaveBlockList | null>(null)
const form = ref<Partial<LeaveBlockList> & { dates: Partial<LeaveBlockListDate>[] }>({ dates: [] })
const saving = ref(false)
const errorMsg = ref('')

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'applies_to_company', label: 'Company-wide' },
  { key: 'is_active', label: 'Active' },
]

async function load() {
  loading.value = true
  try { rows.value = await listLeaveBlockLists(true) } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() {
  selected.value = null
  form.value = { is_active: 1, applies_to_company: 1, dates: [{ block_date: '', reason: '' }] }
  errorMsg.value = ''; drawerOpen.value = true
}
function openEdit(row: LeaveBlockList) {
  selected.value = row
  form.value = { ...row, dates: row.dates.map(d => ({ ...d })) }
  errorMsg.value = ''; drawerOpen.value = true
}

function addDate() { form.value.dates.push({ block_date: '', reason: '' }) }
function removeDate(i: number) { form.value.dates.splice(i, 1) }

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    const payload = { ...form.value }
    if (selected.value) await updateLeaveBlockList(selected.value.id, { name: payload.name, applies_to_company: payload.applies_to_company, is_active: payload.is_active })
    else await createLeaveBlockList(payload)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}
</script>

<template>
  <div class="space-y-8">
    <PageHeader 
      title="Leave Block Lists" 
      subtitle="Define dates on which leave is blocked" 
      action-label="New Block List" 
      @action="openCreate" 
    />
    
    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="No block lists yet.">
      <template #cell-applies_to_company="{ value }">
        <span 
          :class="value ? 'bg-indigo-100/50 text-indigo-700 border-indigo-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50'" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
        >
          {{ value ? 'Yes' : 'No' }}
        </span>
      </template>
      <template #cell-is_active="{ value }">
        <span 
          :class="value ? 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50'" 
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border shadow-sm"
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

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Block List' : 'Create Leave Block List'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <FormInput label="List Name" :modelValue="form.name" @update:modelValue="form.name = $event" placeholder="e.g. Peak Season Blocks" required />
        
        <div class="flex flex-wrap gap-4">
          <div class="flex items-center space-x-2 bg-muted/30 p-3 px-4 rounded-xl border border-dashed flex-1 min-w-[140px]">
            <Checkbox id="bl-company" :checked="!!form.applies_to_company" @update:checked="form.applies_to_company = $event ? 1 : 0" />
            <Label for="bl-company" class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">Company-wide</Label>
          </div>
          <div class="flex items-center space-x-2 bg-muted/30 p-3 px-4 rounded-xl border border-dashed flex-1 min-w-[140px]">
            <Checkbox id="bl-active" :checked="!!form.is_active" @update:checked="form.is_active = $event ? 1 : 0" />
            <Label for="bl-active" class="text-[10px] font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">Active</Label>
          </div>
        </div>

        <div v-if="!selected" class="space-y-4">
          <div class="flex items-center justify-between">
            <h4 class="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Blocked Dates</h4>
            <Button variant="ghost" size="sm" @click="addDate" class="h-7 text-[10px] font-bold uppercase gap-1 hover:bg-slate-100">
              <Plus class="w-3 h-3" /> Add Date
            </Button>
          </div>

          <div class="space-y-3">
            <div v-for="(d, i) in form.dates" :key="i" class="p-4 rounded-xl border border-slate-200/60 bg-muted/10 animate-in fade-in slide-in-from-top-1">
              <div class="grid grid-cols-12 gap-4 items-end">
                <div class="col-span-12 sm:col-span-4">
                  <FormInput label="Date" type="date" :modelValue="d.block_date" @update:modelValue="d.block_date = $event" />
                </div>
                <div class="col-span-10 sm:col-span-7">
                  <FormInput label="Reason" :modelValue="d.reason" @update:modelValue="d.reason = $event" placeholder="e.g. System upgrade" />
                </div>
                <div class="col-span-2 sm:col-span-1 flex justify-end">
                  <Button variant="ghost" size="icon" @click="removeDate(i)" class="h-9 w-9 text-slate-400 hover:text-destructive hover:bg-destructive/10 rounded-lg">
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
              {{ saving ? 'Saving...' : 'Save Block List' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
