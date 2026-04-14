<script setup lang="ts">
import { ref, reactive, watch, onMounted } from 'vue'
import { CalendarDaysIcon, PlusIcon, XIcon } from 'lucide-vue-next'
import { createLeavePolicy } from '../../../services/leave-policy.service'
import { apiFetchData } from '../../../services/http'
import { handleApiError } from '../../../utils/handleApiError'

const DRAFT_KEY = 'onboarding_draft_leave_types'

const emit = defineEmits<{ completed: []; skipped: [] }>()
defineProps<{ readonly?: boolean }>()

interface LeaveRow { name: string; days: number | '' }

const saving = ref(false)
const errorMsg = ref('')
const policyName = ref('Default Leave Policy')
const rows = ref<LeaveRow[]>([
  { name: 'Casual Leave', days: 12 },
  { name: 'Sick Leave', days: 10 },
  { name: 'Earned Leave', days: 15 },
])

// Draft persistence
watch([policyName, rows], () => {
  localStorage.setItem(DRAFT_KEY, JSON.stringify({ policyName: policyName.value, rows: rows.value }))
}, { deep: true })

onMounted(() => {
  const saved = localStorage.getItem(DRAFT_KEY)
  if (saved) {
    try {
      const d = JSON.parse(saved)
      if (d.policyName) policyName.value = d.policyName
      if (d.rows?.length) rows.value = d.rows
    } catch {}
  }
})

function addRow() {
  rows.value.push({ name: '', days: '' })
}

function removeRow(i: number) {
  if (rows.value.length > 1) rows.value.splice(i, 1)
}

async function submit() {
  if (saving.value) return
  if (!policyName.value.trim()) { errorMsg.value = 'Policy name is required'; return }
  const validRows = rows.value.filter(r => r.name.trim() && Number(r.days) > 0)
  if (validRows.length === 0) { errorMsg.value = 'Add at least one leave type with valid days'; return }

  saving.value = true
  errorMsg.value = ''
  try {
    // Step 1: create each leave type and collect IDs
    const leaveTypeIds: string[] = []
    for (const row of validRows) {
      const lt = await apiFetchData<{ id: string }>('/leave-types/', {
        method: 'POST',
        body: JSON.stringify({
          name: row.name.trim(),
          days_allowed: Number(row.days),
          requires_approval: true,
          is_active: true,
        }),
      })
      leaveTypeIds.push(lt.id)
    }

    // Step 2: create the policy referencing those IDs
    await createLeavePolicy({
      name: policyName.value.trim(),
      items: leaveTypeIds.map((leave_type_id, i) => ({
        leave_type_id,
        annual_allocation: Number(validRows[i].days),
      })) as any,
    })
    localStorage.removeItem(DRAFT_KEY)
    emit('completed')
  } catch (e) {
    errorMsg.value = handleApiError(e)
  } finally {
    saving.value = false
  }
}

function skip() {
  localStorage.removeItem(DRAFT_KEY)
  emit('skipped')
}
</script>

<template>
  <div class="max-w-lg">
    <div class="flex items-center space-x-3 mb-8">
      <div class="w-11 h-11 bg-slate-100 rounded-[14px] flex items-center justify-center">
        <CalendarDaysIcon class="w-5 h-5 text-slate-600" />
      </div>
      <div>
        <h2 class="text-xl font-bold text-slate-900 leading-tight">Configure leave policies</h2>
        <p class="text-sm text-slate-400 font-medium mt-0.5">Define leave types and annual allocations</p>
      </div>
    </div>

    <div v-if="readonly" class="p-4 bg-slate-50 border border-slate-200 rounded-[14px] text-sm text-slate-500 font-medium mb-6">
      This step has been configured. Contact an admin to make changes.
    </div>

    <div v-else class="space-y-5">
      <div>
        <label class="block text-sm font-semibold text-slate-700 mb-1.5">Policy Name <span class="text-rose-500">*</span></label>
        <input
          v-model="policyName"
          type="text"
          placeholder="e.g. Standard Leave Policy"
          class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
        />
      </div>

      <!-- Leave type rows -->
      <div>
        <div class="flex items-center justify-between mb-2">
          <label class="text-sm font-semibold text-slate-700">Leave Types</label>
          <button @click="addRow" class="flex items-center space-x-1 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors">
            <PlusIcon class="w-3.5 h-3.5" />
            <span>Add type</span>
          </button>
        </div>
        <div class="space-y-2">
          <div
            v-for="(row, i) in rows"
            :key="i"
            class="flex items-center space-x-2"
          >
            <input
              v-model="row.name"
              type="text"
              placeholder="Leave name"
              class="flex-1 bg-white border border-slate-200 text-slate-900 text-sm rounded-[10px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-3 py-2.5 outline-none transition-all"
            />
            <input
              v-model="row.days"
              type="number"
              min="1"
              max="365"
              placeholder="Days"
              class="w-20 bg-white border border-slate-200 text-slate-900 text-sm rounded-[10px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-3 py-2.5 outline-none transition-all text-center"
            />
            <button
              @click="removeRow(i)"
              :disabled="rows.length <= 1"
              class="p-2 text-slate-300 hover:text-rose-400 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <XIcon class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <p v-if="errorMsg" class="text-sm text-rose-600 font-medium">{{ errorMsg }}</p>

      <div class="flex items-center space-x-3 pt-2">
        <button
          @click="submit"
          :disabled="saving"
          class="px-7 py-3 bg-slate-900 text-white rounded-full text-sm font-semibold hover:bg-slate-800 transition-all disabled:opacity-60 disabled:cursor-not-allowed flex items-center space-x-2"
        >
          <div v-if="saving" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span>{{ saving ? 'Saving...' : 'Save Leave Policy' }}</span>
        </button>
        <button @click="skip" :disabled="saving" class="px-5 py-3 text-slate-400 hover:text-slate-600 text-sm font-medium transition-colors">
          Skip for now
        </button>
      </div>
    </div>
  </div>
</template>
