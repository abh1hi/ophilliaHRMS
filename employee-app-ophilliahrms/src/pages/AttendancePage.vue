<template>
  <div>
    <!-- ── Saffron Header ── -->
    <div class="saffron-header px-5 pt-10 pb-5">
      <div class="d-flex align-center justify-space-between">
        <div>
          <h1 class="text-h6 font-weight-bold" style="color:#FFFFFF;">Attendance</h1>
          <p class="text-caption" style="color:rgba(255,255,255,0.8);">{{ todayDate }}</p>
        </div>
        <div class="text-right">
          <p class="text-h5 font-weight-black font-mono" style="color:#FFFFFF;">{{ liveTime }}</p>
        </div>
      </div>
    </div>

    <div class="pa-4 pb-nav">

      <!-- ─── LOADING ─── -->
      <div v-if="state === 'loading'" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="48" class="mb-4" />
        <p class="text-body-2" style="color:#79747E;">Loading today's record…</p>
      </div>

      <!-- ─── IDLE ─── -->
      <template v-else-if="state === 'idle'">
        <!-- GPS status -->
        <v-card elevation="0" class="mb-4" style="background:#FFF3E0; border:1px solid rgba(255,153,51,0.25);">
          <v-card-text class="d-flex align-center gap-3 pa-4">
            <v-icon :color="gpsLat ? 'success' : 'warning'" size="20">mdi-map-marker-outline</v-icon>
            <span class="text-body-2 flex-grow-1" style="color:#49454F;">{{ gpsLabel }}</span>
            <v-btn :loading="gpsLoading" icon="mdi-refresh" variant="text" size="small" color="primary" @click="fetchGPS" id="refresh-gps-btn" />
          </v-card-text>
        </v-card>

        <!-- Punch In -->
        <v-btn
          id="punch-in-btn"
          color="primary"
          block
          size="x-large"
          rounded="xl"
          elevation="2"
          prepend-icon="mdi-hand-wave-outline"
          class="text-none"
          style="font-weight:600; height:56px; font-size:16px;"
          @click="startPunchIn"
        >Punch In</v-btn>
        <p class="text-caption text-center mt-3" style="color:#79747E;">You haven't punched in yet today.</p>
      </template>

      <!-- ─── PUNCHING IN (GPS) ─── -->
      <div v-else-if="state === 'punching-in'" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="48" class="mb-4" />
        <p class="text-body-2" style="color:#79747E;">Capturing GPS location…</p>
      </div>

      <!-- ─── TASK ENTRY ─── -->
      <template v-else-if="state === 'task-entry'">
        <v-alert
          variant="tonal"
          density="compact"
          rounded="xl"
          class="mb-4"
          icon="mdi-map-marker-check"
          style="background:#FFF3E0; border:1px solid rgba(255,153,51,0.3);"
          color="primary"
        >
          {{ clockInLocationLabel }} · Add your planned tasks, then confirm punch in.
        </v-alert>

        <!-- Draft tasks list -->
        <v-list v-if="draftTasks.length" density="compact" class="mb-3 rounded-xl overflow-hidden" elevation="1" style="background:#FFFFFF;">
          <v-list-item v-for="(t, i) in draftTasks" :key="i" class="px-4 py-2">
            <template #prepend>
              <v-avatar color="primary-container" variant="flat" size="28" class="mr-3">
                <span class="text-caption font-weight-bold" style="color:#4A2000;">{{ i + 1 }}</span>
              </v-avatar>
            </template>
            <v-list-item-title class="text-body-2 font-weight-medium">{{ t.title }}</v-list-item-title>
            <v-list-item-subtitle v-if="t.estimated_finish_time || t.expected_expenses" class="text-caption">
              <span v-if="t.estimated_finish_time">⏰ {{ t.estimated_finish_time }}</span>
              <span v-if="t.expected_expenses" class="ml-2">₹{{ t.expected_expenses }}</span>
            </v-list-item-subtitle>
            <template #append>
              <v-btn icon="mdi-pencil-outline" variant="text" size="x-small" color="primary" @click="editDraftTask(i)" />
              <v-btn icon="mdi-trash-can-outline" variant="text" size="x-small" color="error" @click="deleteDraftTask(i)" />
            </template>
          </v-list-item>
        </v-list>

        <!-- Add/Edit task form -->
        <v-card class="mb-4" elevation="0" style="border:1px solid rgba(255,153,51,0.25);">
          <v-card-title class="text-subtitle-2 pa-4 pb-2 d-flex align-center gap-2" style="color:#1C1B1F;">
            <v-icon color="primary" size="18">{{ editingTaskIdx !== null ? 'mdi-pencil' : 'mdi-plus-circle-outline' }}</v-icon>
            {{ editingTaskIdx !== null ? 'Edit Task' : 'Add Task' }}
          </v-card-title>
          <v-card-text class="pt-0">
            <v-text-field v-model="taskForm.title" id="task-title-input" label="Task Title *" density="compact" class="mb-2" maxlength="200" />
            <v-textarea v-model="taskForm.details" id="task-details-input" label="Details (optional)" density="compact" rows="2" class="mb-2" />
            <v-row dense>
              <v-col cols="6">
                <v-text-field v-model="taskForm.estimated_finish_time" id="task-finish-input" label="Est. Finish Time" density="compact" placeholder="6:30 PM" />
              </v-col>
              <v-col cols="6">
                <v-text-field v-model.number="taskForm.expected_expenses" id="task-expenses-input" label="Est. Expenses (₹)" density="compact" type="number" min="0" />
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="px-4 pb-4 pt-0">
            <v-btn v-if="editingTaskIdx !== null" variant="outlined" color="primary" rounded="xl" class="text-none" @click="cancelEdit" id="cancel-edit-btn">Cancel</v-btn>
            <v-spacer />
            <v-btn id="save-task-btn" color="primary" variant="tonal" rounded="xl" class="text-none" :disabled="!taskForm.title.trim()" @click="saveTaskDraft">
              {{ editingTaskIdx !== null ? 'Update Task' : 'Add Task' }}
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-alert v-if="taskError" type="error" variant="tonal" density="compact" rounded="xl" class="mb-3">{{ taskError }}</v-alert>

        <v-btn
          id="confirm-punch-in-btn"
          color="primary" block size="x-large" rounded="xl" elevation="2"
          prepend-icon="mdi-check-circle-outline"
          class="text-none"
          style="font-weight:600; height:56px; font-size:16px;"
          :loading="submitting"
          @click="confirmPunchIn"
        >Confirm Punch In</v-btn>
      </template>

      <!-- ─── DAY ACTIVE ─── -->
      <template v-else-if="state === 'day-active'">

        <!-- Punch-in summary -->
        <v-card class="mb-4" elevation="1" style="border-left:4px solid #2E7D32; background:#F1F8E9;">
          <v-card-text class="pa-4">
            <div class="d-flex align-center gap-3">
              <v-avatar color="success" variant="tonal" size="44">
                <v-icon color="success" size="22">mdi-timeline-clock</v-icon>
              </v-avatar>
              <div class="flex-grow-1">
                <p class="text-caption font-weight-bold mb-0" style="color:#79747E; letter-spacing:0.8px;">PUNCHED IN</p>
                <p class="text-h6 font-weight-bold mb-0" style="color:#2E7D32;">{{ formatTime(record!.clock_in) }}</p>
                <p v-if="record!.clock_in_location_name" class="text-caption" style="color:#49454F;">📍 {{ record!.clock_in_location_name }}</p>
              </div>
              <div class="text-right">
                <p class="text-h5 font-weight-black font-mono" style="color:#FF9933;">{{ elapsedTime }}</p>
                <p class="text-caption" style="color:#79747E;">elapsed</p>
              </div>
            </div>
          </v-card-text>
        </v-card>

        <!-- Tasks header -->
        <div class="d-flex align-center justify-space-between mb-2">
          <p class="section-label">Today's Tasks</p>
          <v-btn id="add-task-btn" size="small" variant="tonal" color="primary" rounded="xl" class="text-none"
            :prepend-icon="showAddTaskForm ? 'mdi-close' : 'mdi-plus'"
            @click="showAddTaskForm = !showAddTaskForm">
            {{ showAddTaskForm ? 'Cancel' : 'Add Task' }}
          </v-btn>
        </div>

        <!-- Mid-day add task form -->
        <v-card v-if="showAddTaskForm" class="mb-3" elevation="0" style="border:1px solid rgba(255,153,51,0.25);">
          <v-card-text class="pb-2">
            <v-text-field v-model="taskForm.title" id="mid-day-title" label="Task Title *" density="compact" class="mb-2" />
            <v-textarea v-model="taskForm.details" id="mid-day-details" label="Details" density="compact" rows="2" class="mb-2" />
            <v-row dense>
              <v-col cols="6"><v-text-field v-model="taskForm.estimated_finish_time" label="Est. Finish" density="compact" placeholder="6:30 PM" /></v-col>
              <v-col cols="6"><v-text-field v-model.number="taskForm.expected_expenses" label="Est. Expenses (₹)" density="compact" type="number" min="0" /></v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="pa-4 pt-0">
            <v-spacer />
            <v-btn id="save-midday-task-btn" color="primary" variant="tonal" :loading="submitting" :disabled="!taskForm.title.trim()" rounded="xl" class="text-none" @click="addLiveTask">Save Task</v-btn>
          </v-card-actions>
        </v-card>

        <!-- Task list -->
        <v-list v-if="record?.tasks?.length" density="compact" class="rounded-xl mb-4 overflow-hidden" elevation="1" style="background:#FFFFFF;">
          <v-list-item v-for="t in record!.tasks" :key="t.id" class="px-4 py-3">
            <template #prepend>
              <v-icon :color="taskColor(t.status)" size="18" class="mr-3">{{ taskIcon(t.status) }}</v-icon>
            </template>
            <v-list-item-title class="text-body-2 font-weight-medium">{{ t.title }}</v-list-item-title>
            <v-list-item-subtitle v-if="t.estimated_finish_time" class="text-caption">⏰ {{ t.estimated_finish_time }}</v-list-item-subtitle>
            <template #append>
              <v-chip :color="taskColor(t.status)" size="x-small" variant="tonal">{{ taskLabel(t.status) }}</v-chip>
            </template>
          </v-list-item>
        </v-list>
        <v-card v-else elevation="0" class="mb-4 text-center py-4" style="background:#FFF3E0;">
          <p class="text-body-2" style="color:#79747E;">No tasks yet. Add your first task above.</p>
        </v-card>

        <!-- Assign to colleague -->
        <v-divider class="my-4" style="border-color:rgba(255,153,51,0.2);" />
        <div class="d-flex align-center justify-space-between mb-2">
          <p class="section-label">Assign Task to Colleague</p>
          <v-btn id="toggle-assign-btn" size="small" variant="tonal" color="secondary" rounded="xl" class="text-none"
            :prepend-icon="showAssignForm ? 'mdi-close' : 'mdi-account-arrow-right-outline'"
            @click="showAssignForm = !showAssignForm">
            {{ showAssignForm ? 'Cancel' : 'Assign' }}
          </v-btn>
        </div>
        <v-card v-if="showAssignForm" class="mb-3" elevation="0" style="border:1px solid rgba(179,92,0,0.25);">
          <v-card-text class="pb-2">
            <v-text-field v-model="assignForm.target_employee_id" id="assign-emp-id" label="Colleague Employee ID *" density="compact" class="mb-2" hint="Enter the target employee's ID" persistent-hint />
            <v-text-field v-model="assignForm.title" id="assign-title" label="Task Title *" density="compact" class="mb-2" />
            <v-textarea v-model="assignForm.details" id="assign-details" label="Details" density="compact" rows="2" class="mb-2" />
            <v-row dense>
              <v-col cols="6"><v-text-field v-model="assignForm.estimated_finish_time" label="Est. Finish" density="compact" placeholder="6:30 PM" /></v-col>
              <v-col cols="6"><v-text-field v-model.number="assignForm.expected_expenses" label="Est. Expenses (₹)" density="compact" type="number" min="0" /></v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="pa-4 pt-0">
            <v-spacer />
            <v-btn id="save-assign-btn" color="secondary" variant="tonal" :loading="assignSubmitting"
              :disabled="!assignForm.title.trim() || !assignForm.target_employee_id.trim()"
              rounded="xl" class="text-none" @click="submitAssignTask">Assign Task</v-btn>
          </v-card-actions>
        </v-card>
        <v-alert v-if="assignError"   type="error"   variant="tonal" density="compact" rounded="xl" class="mb-2">{{ assignError }}</v-alert>
        <v-alert v-if="assignSuccess" type="success" variant="tonal" density="compact" rounded="xl" class="mb-2">{{ assignSuccess }}</v-alert>
        <v-alert v-if="taskError"     type="error"   variant="tonal" density="compact" rounded="xl" class="mb-3">{{ taskError }}</v-alert>

        <!-- Punch Out -->
        <v-btn
          id="punch-out-btn"
          color="error" block size="x-large" rounded="xl" elevation="2"
          prepend-icon="mdi-flag-checkered"
          class="text-none mt-2"
          style="font-weight:600; height:56px; font-size:16px;"
          @click="startPunchOut"
        >Punch Out</v-btn>
      </template>

      <!-- ─── PUNCH-OUT REVIEW ─── -->
      <template v-else-if="state === 'punch-out-review'">
        <v-alert variant="tonal" density="compact" rounded="xl" class="mb-4" icon="mdi-clipboard-edit-outline" color="primary" style="background:#FFF3E0; border:1px solid rgba(255,153,51,0.3);">
          Review each task's outcome before punching out.
        </v-alert>

        <v-card v-for="(tc, i) in taskCompletions" :key="tc.task_id" class="mb-3" elevation="0" style="border:1px solid rgba(255,153,51,0.2);">
          <v-card-title class="text-body-2 font-weight-bold pa-4 pb-2" style="color:#1C1B1F;">
            <v-icon size="16" color="primary" class="mr-2">mdi-checkbox-marked-circle-outline</v-icon>
            {{ tc.title }}
          </v-card-title>
          <v-card-text class="pt-1">
            <v-select
              v-model="tc.status"
              :id="'task-status-' + i"
              label="Task Status"
              density="compact"
              :items="[
                { title: '✅ Completed', value: 'completed' },
                { title: '⚡ Partially Completed', value: 'partially_completed' },
                { title: '❌ Not Completed', value: 'not_completed' },
              ]"
              item-title="title" item-value="value"
              class="mb-2"
            />
            <v-textarea :id="'task-notes-' + i" v-model="tc.completion_notes" label="Completion Notes" density="compact" rows="2" class="mb-2" />
            <v-text-field :id="'task-exp-' + i" v-model.number="tc.actual_expenses" label="Actual Expenses (₹)" density="compact" type="number" min="0" />
          </v-card-text>
        </v-card>

        <v-card v-if="!taskCompletions.length" elevation="0" class="mb-4 text-center py-4" style="background:#FFF3E0;">
          <p class="text-body-2" style="color:#79747E;">No tasks to review.</p>
        </v-card>

        <v-btn id="go-to-rating-btn" color="primary" block size="large" rounded="xl" class="text-none" style="font-weight:600; height:52px;" append-icon="mdi-arrow-right" @click="state = 'rating'">
          Next: Rate Your Day
        </v-btn>
      </template>

      <!-- ─── RATING ─── -->
      <template v-else-if="state === 'rating'">
        <v-card class="mb-4 text-center pa-6" elevation="0" style="border:1px solid rgba(255,153,51,0.2);">
          <div class="mb-4" style="font-size:48px;">🌟</div>
          <h2 class="text-h6 font-weight-bold mb-2" style="color:#1C1B1F;">How was your day?</h2>
          <p class="text-body-2 mb-6" style="color:#49454F;">Your honest self-assessment helps track productivity.</p>

          <!-- Star rating -->
          <div class="d-flex justify-center gap-1 mb-5">
            <v-btn
              v-for="n in 5" :key="n"
              :id="'star-' + n"
              :icon="dayRating >= n ? 'mdi-star' : 'mdi-star-outline'"
              :color="dayRating >= n ? '#FF9933' : '#CAC4D0'"
              variant="text"
              size="x-large"
              @click="dayRating = n"
            />
          </div>

          <v-chip v-if="dayRating" color="primary" variant="tonal" size="large" class="font-weight-bold">
            {{ ratingLabel }}
          </v-chip>
          <p v-else class="text-caption" style="color:#79747E;">Tap a star to rate</p>
        </v-card>

        <v-alert v-if="punchOutError" type="error" variant="tonal" density="compact" rounded="xl" class="mb-3">{{ punchOutError }}</v-alert>

        <v-btn
          id="confirm-punch-out-btn"
          color="error" block size="x-large" rounded="xl" elevation="2"
          prepend-icon="mdi-flag-checkered"
          class="text-none"
          style="font-weight:600; height:56px; font-size:16px;"
          :loading="submitting"
          :disabled="!dayRating"
          @click="confirmPunchOut"
        >Confirm Punch Out</v-btn>
      </template>

      <!-- ─── DONE ─── -->
      <template v-else-if="state === 'done'">
        <!-- Celebration card -->
        <v-card class="mb-4 text-center pa-6" elevation="0" style="background:linear-gradient(135deg,#FFF3E0,#FFFBF5); border:1px solid rgba(255,153,51,0.25);">
          <div style="font-size:52px;" class="mb-3">🎉</div>
          <h2 class="text-h5 font-weight-black mb-1" style="color:#1C1B1F;">Day Complete!</h2>
          <p class="text-body-2 mb-6" style="color:#49454F;">Great work today, {{ emp.first_name }}.</p>

          <!-- Stats -->
          <v-row class="mb-5">
            <v-col v-for="s in doneStats" :key="s.label" cols="4" class="text-center">
              <p class="text-h6 font-weight-black" style="color:#FF9933;">{{ s.value }}</p>
              <p class="text-caption" style="color:#79747E;">{{ s.label }}</p>
            </v-col>
          </v-row>

          <v-divider style="border-color:rgba(255,153,51,0.15);" class="mb-4" />

          <!-- Task summary -->
          <v-list density="compact" class="text-left rounded-xl py-0" bg-color="transparent">
            <v-list-item v-for="t in record?.tasks" :key="t.id" class="px-2">
              <template #prepend>
                <v-icon :color="taskColor(t.status)" size="16" class="mr-2">{{ taskIcon(t.status) }}</v-icon>
              </template>
              <v-list-item-title class="text-body-2">{{ t.title }}</v-list-item-title>
              <template #append>
                <v-chip :color="taskColor(t.status)" size="x-small" variant="tonal">{{ taskLabel(t.status) }}</v-chip>
              </template>
            </v-list-item>
          </v-list>

          <template v-if="record?.clock_in_location_name || record?.clock_out_location_name">
            <v-divider style="border-color:rgba(255,153,51,0.15);" class="my-3" />
            <p v-if="record?.clock_in_location_name" class="text-caption" style="color:#49454F;">🟢 Start: {{ record.clock_in_location_name }}</p>
            <p v-if="record?.clock_out_location_name" class="text-caption" style="color:#49454F;">🏁 End: {{ record.clock_out_location_name }}</p>
          </template>
        </v-card>
      </template>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import {
  getTodayRecord, clockIn, clockOut, addTask, getCurrentPosition, assignTaskToEmployee,
} from '../services/attendance'
import type { AttendanceRecord, TaskCompleteItem, TaskAssignRequest } from '../services/attendance'

const props = defineProps<{ employee: any }>()
const emp = computed(() => props.employee)

type PageState = 'loading' | 'idle' | 'punching-in' | 'task-entry' | 'day-active' | 'punch-out-review' | 'rating' | 'done'
const state      = ref<PageState>('loading')
const record     = ref<AttendanceRecord | null>(null)
const submitting = ref(false)
const taskError  = ref('')
const punchOutError = ref('')

// GPS
const gpsLat    = ref<number | null>(null)
const gpsLng    = ref<number | null>(null)
const gpsLoading = ref(false)
const gpsLabel  = computed(() =>
  gpsLoading.value ? 'Fetching GPS…' :
  gpsLat.value     ? `${gpsLat.value.toFixed(4)}, ${gpsLng.value?.toFixed(4)}` :
                     'GPS location not available'
)
const clockInLocationLabel = computed(() =>
  gpsLat.value ? `📍 ${gpsLat.value.toFixed(4)}, ${gpsLng.value?.toFixed(4)}` : 'No GPS location captured'
)

// Live clock
const liveTime = ref('')
let clockTick: ReturnType<typeof setInterval>

// Draft tasks
const draftTasks     = ref<any[]>([])
const editingTaskIdx = ref<number | null>(null)
const showAddTaskForm = ref(false)
const taskForm = ref({ title: '', details: '', estimated_finish_time: '', expected_expenses: undefined as number | undefined })

// Assign to colleague
const showAssignForm   = ref(false)
const assignSubmitting = ref(false)
const assignError      = ref('')
const assignSuccess    = ref('')
const assignForm = ref<TaskAssignRequest & { target_employee_id: string }>({
  target_employee_id: '', title: '', details: '', estimated_finish_time: '', expected_expenses: undefined as any,
})

// Punch-out
const dayRating      = ref(0)
const taskCompletions = ref<Array<TaskCompleteItem & { title: string }>>([])

// ── Computed ───────────────────────────────────────────────────────────────
const todayDate = computed(() =>
  new Date().toLocaleDateString('en-IN', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' })
)
const elapsedTime = computed(() => {
  if (!record.value?.clock_in) return ''
  const diff = Date.now() - new Date(record.value.clock_in).getTime()
  const h = Math.floor(diff / 3600000), m = Math.floor((diff % 3600000) / 60000)
  return `${h}h ${m}m`
})
const ratingLabel = computed(() =>
  ['', 'Very Poor', 'Poor', 'Average', 'Good', 'Excellent'][dayRating.value] ?? ''
)
const doneStats = computed(() => [
  { label: 'Work Hours', value: `${record.value?.work_hours?.toFixed(1) ?? '–'}h` },
  { label: 'Overtime',   value: `${record.value?.overtime_hours?.toFixed(1) ?? '0'}h` },
  { label: 'Rating',     value: '⭐'.repeat(record.value?.day_rating ?? 0) || '–' },
])

// ── Helpers ────────────────────────────────────────────────────────────────
function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })
}
function taskColor(s: string) {
  return ({ pending: 'warning', completed: 'success', partially_completed: 'primary', not_completed: 'error' } as any)[s] ?? 'default'
}
function taskIcon(s: string) {
  return ({ pending: 'mdi-circle-outline', completed: 'mdi-check-circle', partially_completed: 'mdi-circle-half-full', not_completed: 'mdi-close-circle' } as any)[s] ?? 'mdi-circle'
}
function taskLabel(s: string) {
  return ({ pending: 'Pending', completed: 'Done', partially_completed: 'Partial', not_completed: 'Not Done' } as any)[s] ?? s
}

// ── GPS ────────────────────────────────────────────────────────────────────
async function fetchGPS() {
  gpsLoading.value = true
  try { const p = await getCurrentPosition(); gpsLat.value = p.lat; gpsLng.value = p.lng }
  catch { /* GPS optional */ }
  finally { gpsLoading.value = false }
}

// ── Task form ──────────────────────────────────────────────────────────────
function resetForm() { taskForm.value = { title: '', details: '', estimated_finish_time: '', expected_expenses: undefined }; editingTaskIdx.value = null }
function saveTaskDraft() {
  if (!taskForm.value.title.trim()) return
  editingTaskIdx.value !== null
    ? (draftTasks.value[editingTaskIdx.value] = { ...taskForm.value })
    : draftTasks.value.push({ ...taskForm.value })
  resetForm()
}
function editDraftTask(i: number) {
  taskForm.value = { ...draftTasks.value[i], details: draftTasks.value[i].details ?? '', estimated_finish_time: draftTasks.value[i].estimated_finish_time ?? '' }
  editingTaskIdx.value = i
}
function deleteDraftTask(i: number) { draftTasks.value.splice(i, 1); if (editingTaskIdx.value === i) resetForm() }
function cancelEdit() { resetForm() }

// ── Punch In ──────────────────────────────────────────────────────────────
async function startPunchIn() { state.value = 'punching-in'; await fetchGPS(); state.value = 'task-entry' }

async function confirmPunchIn() {
  if (submitting.value) return
  submitting.value = true; taskError.value = ''
  try {
    const r = await clockIn(gpsLat.value, gpsLng.value, gpsLat.value ? gpsLabel.value : undefined)
    record.value = r
    for (const t of draftTasks.value) {
      const saved = await addTask(r.id, t)
      record.value.tasks = [...(record.value.tasks ?? []), saved]
    }
    draftTasks.value = []
    state.value = 'day-active'
  } catch (e: any) { taskError.value = e.message ?? 'Failed to punch in'; state.value = 'task-entry' }
  finally { submitting.value = false }
}

// ── Mid-day task ───────────────────────────────────────────────────────────
async function addLiveTask() {
  if (!taskForm.value.title.trim() || !record.value) return
  submitting.value = true; taskError.value = ''
  try {
    const t = await addTask(record.value.id, { ...taskForm.value })
    record.value.tasks = [...(record.value.tasks ?? []), t]
    resetForm(); showAddTaskForm.value = false
  } catch (e: any) { taskError.value = e.message ?? 'Failed to add task' }
  finally { submitting.value = false }
}

// ── Assign task to colleague ───────────────────────────────────────────────
async function submitAssignTask() {
  if (!assignForm.value.title.trim() || !assignForm.value.target_employee_id.trim()) return
  assignSubmitting.value = true; assignError.value = ''; assignSuccess.value = ''
  try {
    await assignTaskToEmployee({
      target_employee_id: assignForm.value.target_employee_id.trim(),
      title: assignForm.value.title.trim(),
      details: assignForm.value.details || undefined,
      estimated_finish_time: assignForm.value.estimated_finish_time || undefined,
      expected_expenses: assignForm.value.expected_expenses || undefined,
    })
    assignSuccess.value = 'Task assigned to colleague successfully.'
    assignForm.value = { target_employee_id: '', title: '', details: '', estimated_finish_time: '', expected_expenses: undefined as any }
    showAssignForm.value = false
    setTimeout(() => { assignSuccess.value = '' }, 4000)
  } catch (e: any) { assignError.value = e.message ?? 'Failed to assign task' }
  finally { assignSubmitting.value = false }
}

// ── Punch Out ─────────────────────────────────────────────────────────────
function startPunchOut() {
  taskCompletions.value = (record.value?.tasks ?? []).map(t => ({
    task_id: t.id, title: t.title, status: 'completed' as const, completion_notes: '', actual_expenses: undefined,
  }))
  state.value = 'punch-out-review'
}

async function confirmPunchOut() {
  if (submitting.value || !dayRating.value) return
  submitting.value = true; punchOutError.value = ''
  await fetchGPS()
  try {
    const c = taskCompletions.value.map(({ task_id, status, completion_notes, actual_expenses }) => ({
      task_id, status, completion_notes: completion_notes || undefined, actual_expenses: actual_expenses || undefined,
    }))
    const r = await clockOut(gpsLat.value, gpsLng.value, gpsLat.value ? gpsLabel.value : undefined, dayRating.value, c)
    record.value = r; state.value = 'done'
  } catch (e: any) { punchOutError.value = e.message ?? 'Failed to punch out'; state.value = 'rating' }
  finally { submitting.value = false }
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  const tick = () => { liveTime.value = new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }
  tick()
  clockTick = setInterval(tick, 1000)
  fetchGPS()
  try {
    const r = await getTodayRecord()
    if (!r)            state.value = 'idle'
    else if (r.clock_out) { record.value = r; state.value = 'done' }
    else               { record.value = r; state.value = 'day-active' }
  } catch { state.value = 'idle' }
})
onUnmounted(() => clearInterval(clockTick))
</script>
