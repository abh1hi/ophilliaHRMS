<template>
  <div>
    <!-- ── Saffron Header ── -->
    <div class="saffron-header px-5 pt-10 pb-6">
      <h1 class="text-h6 font-weight-bold" style="color:#FFFFFF;">Leave Management</h1>
      <p class="text-caption" style="color:rgba(255,255,255,0.8);">Apply and track your leaves</p>
    </div>

    <div class="pa-4 pb-nav">

      <!-- ── Leave Balances ── -->
      <p class="section-label mb-3">Leave Balances</p>
      <div v-if="loadingBalances" class="text-center py-4">
        <v-progress-circular indeterminate color="primary" size="36" />
      </div>
      <v-row v-else dense class="mb-5">
        <v-col cols="6" v-for="b in balances" :key="b.id">
          <v-card elevation="0" rounded="xl" style="border:1px solid rgba(255,153,51,0.2); background:#FFF3E0;">
            <v-card-text class="text-center pa-4">
              <p class="text-h4 font-weight-black" style="color:#FF9933;">{{ b.total_days - b.used_days - b.pending_days }}</p>
              <p class="text-body-2 font-weight-medium" style="color:#1C1B1F;">{{ b.leave_type.name }}</p>
              <p class="text-caption" style="color:#79747E;">Total: {{ b.total_days }} · Used: {{ b.used_days }}</p>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" v-if="!balances.length && !loadingBalances">
          <v-alert type="info" variant="tonal" density="compact" rounded="xl" color="primary">No balances found for this year.</v-alert>
        </v-col>
      </v-row>

      <!-- ── Apply Leave ── -->
      <div class="d-flex align-center justify-space-between mb-3">
        <p class="section-label">Apply for Leave</p>
        <v-btn size="small" variant="tonal" color="primary" rounded="xl" class="text-none"
          :prepend-icon="showForm ? 'mdi-close' : 'mdi-plus'"
          @click="showForm = !showForm">
          {{ showForm ? 'Cancel' : 'New Request' }}
        </v-btn>
      </div>

      <v-expand-transition>
        <v-card v-if="showForm" elevation="0" rounded="xl" class="mb-5" style="border:1px solid rgba(255,153,51,0.25);">
          <v-card-text class="pa-4">
            <v-alert v-if="formError"   type="error"   variant="tonal" density="compact" rounded="xl" class="mb-4">{{ formError }}</v-alert>
            <v-alert v-if="formSuccess" type="success" variant="tonal" density="compact" rounded="xl" class="mb-4">Leave request submitted successfully!</v-alert>

            <v-form ref="formRef" @submit.prevent="submitLeave">
              <v-select
                v-model="form.leave_type_id"
                :items="leaveTypes"
                item-title="name"
                item-value="id"
                label="Leave Type *"
                density="compact"
                :rules="[v => !!v || 'Required']"
                class="mb-2"
              />
              <v-row dense>
                <v-col cols="6">
                  <v-text-field v-model="form.start_date" type="date" label="Start Date *" density="compact" :rules="[v => !!v || 'Required', validateDates]" />
                </v-col>
                <v-col cols="6">
                  <v-text-field v-model="form.end_date" type="date" label="End Date *" density="compact" :rules="[v => !!v || 'Required', validateDates]" />
                </v-col>
              </v-row>
              <v-select
                v-model="form.duration_type"
                :items="[{title:'Full Day', value:'FULL_DAY'}, {title:'Half Day', value:'HALF_DAY'}]"
                label="Duration"
                density="compact"
                class="mb-2"
                :rules="[validateDuration]"
              />
              <v-switch
                v-model="form.is_emergency"
                label="Emergency Leave (bypasses 3-day notice)"
                color="primary"
                density="compact"
                class="mb-2"
                hide-details
              />
              <p class="text-caption mb-3" style="color:#B3261E;" v-if="!form.is_emergency && !hasThreeDayNotice">
                ⚠ Non-emergency leaves must be applied at least 3 days in advance.
              </p>
              <v-textarea
                v-model="form.reason"
                label="Reason *"
                density="compact"
                rows="3"
                hint="Minimum 10 characters"
                :rules="[v => !!v || 'Required', v => v.length >= 10 || 'Must be at least 10 characters']"
                class="mb-3"
              />
              <v-btn type="submit" color="primary" block size="large" rounded="xl" class="text-none" style="font-weight:600; height:52px;" :loading="submitting">
                Submit Request
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-expand-transition>

      <!-- ── Leave History ── -->
      <p class="section-label mb-3">Leave History</p>
      <div v-if="loadingHistory" class="text-center py-4">
        <v-progress-circular indeterminate color="primary" size="36" />
      </div>
      <v-list v-else density="compact" class="rounded-xl overflow-hidden mb-4" elevation="1" style="background:#FFFFFF;">
        <template v-if="history.length">
          <v-list-item v-for="req in history" :key="req.id" class="px-4 py-3">
            <v-list-item-title class="text-body-2 font-weight-bold" style="color:#1C1B1F;">{{ req.leave_type.name }}</v-list-item-title>
            <v-list-item-subtitle class="text-caption" style="color:#79747E;">
              {{ formatDate(req.start_date) }} → {{ formatDate(req.end_date) }} ({{ req.total_days }} days)
            </v-list-item-subtitle>
            <v-list-item-subtitle class="text-caption mt-1" style="color:#79747E; opacity:0.85;">
              {{ req.reason.slice(0, 60) }}{{ req.reason.length > 60 ? '…' : '' }}
            </v-list-item-subtitle>
            <template #append>
              <v-chip :color="statusColor(req.status)" size="x-small" variant="tonal" class="font-weight-bold">{{ req.status }}</v-chip>
            </template>
          </v-list-item>
        </template>
        <v-list-item v-else class="text-center">
          <v-list-item-title class="text-body-2" style="color:#79747E;">No leave history found.</v-list-item-title>
        </v-list-item>
      </v-list>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getLeaveTypes, getLeaveBalances, getLeaveHistory, applyForLeave } from '../services/leave'
import type { LeaveType, LeaveBalance, LeaveRequest } from '../services/leave'

const props = defineProps<{ employee: any }>()
const emp = computed(() => props.employee)

const loadingBalances = ref(false)
const loadingHistory  = ref(false)
const balances   = ref<LeaveBalance[]>([])
const history    = ref<LeaveRequest[]>([])
const leaveTypes = ref<LeaveType[]>([])

const showForm   = ref(false)
const formRef    = ref()
const submitting = ref(false)
const formError  = ref('')
const formSuccess = ref(false)
const form = ref({
  leave_type_id: '',
  start_date:    '',
  end_date:      '',
  duration_type: 'FULL_DAY',
  is_emergency:  false,
  reason:        '',
})

onMounted(async () => {
  if (!emp.value?.id) return
  loadingBalances.value = true
  loadingHistory.value  = true
  try {
    const [t, b, h] = await Promise.all([
      getLeaveTypes(),
      getLeaveBalances(emp.value.id),
      getLeaveHistory(1),
    ])
    leaveTypes.value = t
    balances.value   = b
    history.value    = h.items
  } catch (err) { console.error('Failed to load leave data', err) }
  finally { loadingBalances.value = false; loadingHistory.value = false }
})

const hasThreeDayNotice = computed(() => {
  if (!form.value.start_date) return true
  const start = new Date(form.value.start_date)
  const today = new Date(); today.setHours(0, 0, 0, 0)
  return Math.ceil((start.getTime() - today.getTime()) / 86400000) >= 3
})

function validateDates() {
  if (!form.value.start_date || !form.value.end_date) return true
  return form.value.start_date <= form.value.end_date || 'End date cannot be before start date'
}
function validateDuration() {
  if (form.value.duration_type === 'HALF_DAY' && form.value.start_date !== form.value.end_date)
    return 'Half day must have the same start and end date'
  return true
}

async function submitLeave() {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  if (!form.value.is_emergency && !hasThreeDayNotice.value) {
    formError.value = 'Notice period not met. Mark as emergency if needed.'
    return
  }
  formError.value = ''; formSuccess.value = false; submitting.value = true
  try {
    const req = await applyForLeave({ employee_id: emp.value.id, ...form.value })
    formSuccess.value = true
    history.value.unshift(req)
    setTimeout(() => {
      showForm.value = false; formSuccess.value = false
      form.value = { leave_type_id: leaveTypes.value[0]?.id || '', start_date: '', end_date: '', duration_type: 'FULL_DAY', is_emergency: false, reason: '' }
    }, 1500)
  } catch (err: any) {
    formError.value = err.message || 'Failed to submit leave request'
  } finally { submitting.value = false }
}

function formatDate(d: string) {
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}
function statusColor(s: string) {
  return ({ PENDING: 'warning', APPROVED: 'success', REJECTED: 'error', CANCELLED: 'default' } as any)[s] || 'default'
}
</script>
