<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import DataTable from '../ui/DataTable.vue'
import SlideDrawer from '../ui/SlideDrawer.vue'
import FormInput from '../ui/FormInput.vue'
import EmptyState from '../ui/EmptyState.vue'
import { Button } from '../ui/button'
import { Checkbox } from '../ui/checkbox'
import { Label } from '../ui/label'
import { Pencil, Trash2, Tag } from 'lucide-vue-next'
import { listLeaveTypes, createLeaveType, updateLeaveType, deleteLeaveType } from '../../services/leave-type.service'
import type { LeaveType } from '../../services/leave-type.service'

const rows = ref<LeaveType[]>([])
const loading = ref(false)
const drawerOpen = ref(false)
const selected = ref<LeaveType | null>(null)
const form = ref<Partial<LeaveType>>({})
const saving = ref(false)
const deleting = ref<string | null>(null)
const errorMsg = ref('')

const columns = [
  { key: 'name',              label: 'Leave Type'          },
  { key: 'days_allowed',      label: 'Days Allowed'        },
  { key: 'requires_approval', label: 'Requires Approval'  },
  { key: 'is_active',         label: 'Status'              },
]

async function load() {
  loading.value = true
  try { rows.value = await listLeaveTypes() } catch {} finally { loading.value = false }
}
onMounted(load)

function openCreate() {
  selected.value = null
  form.value = { requires_approval: true, is_active: true, days_allowed: 0 }
  errorMsg.value = ''
  drawerOpen.value = true
}

function openEdit(row: LeaveType) {
  selected.value = row
  form.value = { ...row }
  errorMsg.value = ''
  drawerOpen.value = true
}

async function save() {
  saving.value = true; errorMsg.value = ''
  try {
    if (selected.value) await updateLeaveType(selected.value.id, form.value)
    else await createLeaveType(form.value)
    drawerOpen.value = false; load()
  } catch (e: any) { errorMsg.value = e.message } finally { saving.value = false }
}

async function remove(id: string) {
  if (!confirm('Delete this leave type? This cannot be undone.')) return
  deleting.value = id
  try { await deleteLeaveType(id); load() } catch {} finally { deleting.value = null }
}
</script>

<template>
  <div class="space-y-8">
    <PageHeader
      title="Leave Types"
      subtitle="Define leave categories and annual entitlements"
      action-label="Add Leave Type"
      @action="openCreate"
    />

    <DataTable :columns="columns" :rows="rows" :loading="loading" :searchable="true" empty-text="">
      <template #empty>
        <EmptyState
          :icon="Tag"
          title="No leave types yet"
          description="Add your first leave type to start managing employee leave entitlements."
          action-label="Add Leave Type"
          @action="openCreate"
        />
      </template>

      <template #cell-requires_approval="{ value }">
        <span
          :class="value ? 'bg-amber-100/50 text-amber-700 border-amber-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50'"
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
        >
          {{ value ? 'Yes' : 'No' }}
        </span>
      </template>

      <template #cell-is_active="{ value }">
        <span
          :class="value ? 'bg-emerald-100/50 text-emerald-700 border-emerald-200/50' : 'bg-slate-100/50 text-slate-500 border-slate-200/50'"
          class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
        >
          {{ value ? 'Active' : 'Inactive' }}
        </span>
      </template>

      <template #actions="{ row }">
        <div class="flex items-center justify-end gap-1">
          <Button variant="ghost" size="icon" @click="openEdit(row)" class="h-8 w-8 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-900">
            <Pencil class="w-4 h-4" />
          </Button>
          <Button variant="ghost" size="icon" @click="remove(row.id)" :disabled="deleting === row.id" class="h-8 w-8 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-600">
            <Trash2 class="w-4 h-4" />
          </Button>
        </div>
      </template>
    </DataTable>

    <SlideDrawer :open="drawerOpen" :title="selected ? 'Edit Leave Type' : 'Add Leave Type'" width="w-full max-w-lg" @close="drawerOpen = false">
      <div class="space-y-6">
        <FormInput
          label="Leave Type Name"
          :modelValue="form.name"
          @update:modelValue="form.name = $event"
          placeholder="e.g. Annual Leave, Sick Leave"
          required
        />

        <FormInput
          label="Days Allowed Per Year"
          type="number"
          :modelValue="String(form.days_allowed ?? 0)"
          @update:modelValue="form.days_allowed = Number($event)"
          placeholder="e.g. 15"
          required
        />

        <div class="flex items-center space-x-2 bg-muted/30 p-4 rounded-xl border border-dashed">
          <Checkbox
            id="lt-approval"
            :checked="!!form.requires_approval"
            @update:checked="form.requires_approval = $event"
          />
          <Label for="lt-approval" class="text-xs font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">
            Requires Manager Approval
          </Label>
        </div>

        <div class="flex items-center space-x-2 bg-muted/30 p-4 rounded-xl border border-dashed">
          <Checkbox
            id="lt-active"
            :checked="!!form.is_active"
            @update:checked="form.is_active = $event"
          />
          <Label for="lt-active" class="text-xs font-bold uppercase tracking-wider text-muted-foreground cursor-pointer">
            Active
          </Label>
        </div>
      </div>

      <template #footer>
        <div class="flex items-center justify-between w-full">
          <p v-if="errorMsg" class="text-xs text-destructive font-medium">{{ errorMsg }}</p>
          <div v-else></div>
          <div class="flex items-center gap-3">
            <Button variant="outline" @click="drawerOpen = false" class="rounded-full px-6">Cancel</Button>
            <Button @click="save" :disabled="saving" class="rounded-full px-8 bg-slate-900 text-white hover:bg-slate-800">
              {{ saving ? 'Saving...' : selected ? 'Update' : 'Create' }}
            </Button>
          </div>
        </div>
      </template>
    </SlideDrawer>
  </div>
</template>
