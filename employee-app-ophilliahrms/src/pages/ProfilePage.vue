<template>
  <div>
    <!-- ── Saffron Header ── -->
    <div class="saffron-header px-5 pt-10 pb-7">
      <div class="d-flex align-center gap-4 mb-4">
        <v-avatar size="64" style="background:rgba(255,255,255,0.25); border:3px solid rgba(255,255,255,0.6);">
          <span class="text-h5 font-weight-black" style="color:#FFFFFF;">{{ initials }}</span>
        </v-avatar>
        <div class="flex-grow-1">
          <h1 class="text-h6 font-weight-black" style="color:#FFFFFF;">{{ emp.first_name }} {{ emp.last_name }}</h1>
          <p class="text-body-2" style="color:rgba(255,255,255,0.85);">{{ emp.designation }}<span v-if="emp.department"> · {{ emp.department }}</span></p>
          <p class="text-caption" style="color:rgba(255,255,255,0.7);" v-if="emp.project">📁 {{ emp.project }}</p>
        </div>
        <v-btn icon="mdi-logout" variant="flat" size="small" style="background:rgba(255,255,255,0.2); color:#FFFFFF;" @click="$emit('logout')" />
      </div>
      <div class="d-flex gap-2 flex-wrap">
        <v-chip color="white" variant="tonal" size="small" style="opacity:0.9;">{{ emp.employment_status }}</v-chip>
        <v-chip color="white" variant="tonal" size="small" v-if="emp.role" style="opacity:0.9;">{{ emp.role }}</v-chip>
        <v-chip color="white" variant="tonal" size="small" v-if="emp.date_joined" style="opacity:0.9;">Joined {{ formatDate(emp.date_joined) }}</v-chip>
      </div>
    </div>

    <!-- ── Tabs ── -->
    <v-tabs v-model="activeTab" color="primary" density="compact" grow
      style="background:#FFFFFF; border-bottom:2px solid rgba(255,153,51,0.18);">
      <v-tab v-for="t in tabs" :key="t.key" :value="t.key" class="text-none" style="font-weight:500;">
        <v-icon size="16" class="mr-1">{{ t.icon }}</v-icon>
        {{ t.label }}
      </v-tab>
    </v-tabs>

    <!-- ── Tab Content ── -->
    <div class="pa-4 pb-nav">
      <v-window v-model="activeTab">

        <v-window-item v-for="tab in tabs" :key="tab.key" :value="tab.key">
          <v-card elevation="0" rounded="xl" style="border:1px solid rgba(255,153,51,0.15);">
            <v-list density="compact" lines="two" bg-color="transparent">
              <template v-for="(row, idx) in tabRows(tab.key)" :key="row.label">
                <v-list-item v-if="row.value" class="px-4 py-3">
                  <v-list-item-title class="text-caption font-weight-bold" style="letter-spacing:0.8px; text-transform:uppercase; color:#79747E;">
                    {{ row.label }}
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-body-2 font-weight-medium mt-1" style="color:#1C1B1F;">
                    {{ row.value }}
                  </v-list-item-subtitle>
                </v-list-item>
                <v-divider v-if="row.value && idx < tabRows(tab.key).length - 1" style="border-color:rgba(255,153,51,0.1);" />
              </template>
              <v-list-item v-if="!tabRows(tab.key).filter(r => r.value).length" class="text-center py-6">
                <v-list-item-title class="text-body-2" style="color:#79747E;">No information available.</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card>
        </v-window-item>

      </v-window>

      <!-- Sign out -->
      <v-btn
        block variant="outlined" color="error" rounded="xl" class="mt-5 text-none"
        prepend-icon="mdi-logout"
        style="font-weight:600; height:50px;"
        @click="$emit('logout')"
      >Sign Out</v-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ employee: any }>()
defineEmits<{ logout: [] }>()
const emp = computed(() => props.employee)
const activeTab = ref('job')

const initials = computed(() =>
  `${emp.value?.first_name?.[0] ?? ''}${emp.value?.last_name?.[0] ?? ''}`.toUpperCase()
)

const tabs = [
  { key: 'job',      label: 'Job',      icon: 'mdi-briefcase-outline'          },
  { key: 'personal', label: 'Personal', icon: 'mdi-account-outline'            },
  { key: 'bank',     label: 'Bank',     icon: 'mdi-bank-outline'               },
  { key: 'ids',      label: 'IDs',      icon: 'mdi-card-account-details-outline' },
]

function formatDate(d: string | null) {
  if (!d) return null
  try { return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) } catch { return d }
}
function currency(n: number | null) {
  if (!n) return null
  return `₹${n.toLocaleString('en-IN')}`
}

function tabRows(key: string) {
  const e = emp.value
  switch (key) {
    case 'job': return [
      { label: 'Designation',       value: e.designation },
      { label: 'Department',        value: e.department },
      { label: 'Project',           value: e.project },
      { label: 'Role',              value: e.role },
      { label: 'Employment Status', value: e.employment_status },
      { label: 'Date Joined',       value: formatDate(e.date_joined) },
      { label: 'Joining Salary',    value: currency(e.joining_salary) },
    ]
    case 'personal': return [
      { label: 'Full Name',         value: `${e.first_name} ${e.last_name}` },
      { label: 'Gender',            value: e.gender },
      { label: 'Date of Birth',     value: formatDate(e.date_of_birth) },
      { label: 'Work Email',        value: e.email },
      { label: 'Personal Email',    value: e.personal_email },
      { label: 'Phone',             value: e.phone },
      { label: 'Phone 2',           value: e.phone_2 },
      { label: 'Door / House No.',  value: e.door_no },
      { label: 'Street',            value: e.street },
      { label: 'Village / Town',    value: e.village_town },
      { label: 'PIN Code',          value: e.pin_code },
      { label: 'Emergency Contact', value: e.emergency_contact_name },
      { label: 'Emergency Phone',   value: e.emergency_contact_number },
      { label: 'Referred By',       value: e.referred_by },
    ]
    case 'bank': return [
      { label: 'Bank Name',        value: e.bank_name },
      { label: 'Branch',           value: e.bank_branch },
      { label: 'Account Number',   value: e.bank_account_number },
      { label: 'IFSC Code',        value: e.ifsc_code },
    ]
    case 'ids': return [
      { label: 'Aadhaar Number',        value: e.aadhaar_number },
      { label: 'PAN Number',            value: e.pan_number },
      { label: 'UAN Number',            value: e.uan_number },
      { label: 'ESI Number',            value: e.esi_number },
      { label: 'Driving Licence',       value: e.driving_license_number },
      { label: 'Highest Qualification', value: e.highest_qualification },
      { label: 'Year of Passing',       value: e.year_of_passing },
      { label: 'Institute',             value: e.institute_name },
    ]
    default: return []
  }
}
</script>
