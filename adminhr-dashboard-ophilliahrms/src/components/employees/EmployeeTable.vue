<script setup lang="ts">
import { Pencil, Trash2, Mail, RefreshCw, XCircle, ShieldOff } from 'lucide-vue-next'
import { Button } from '../ui/button'
import { Checkbox } from '../ui/checkbox'
import DataTable from '../ui/DataTable.vue'
import EmployeeStatusBadge from './EmployeeStatusBadge.vue'
import AccountStatusBadge from './AccountStatusBadge.vue'
import type { Employee } from '../../services/employee.service'

const props = defineProps<{
  employees: Employee[]
  loading: boolean
  total: number
  page: number
  selectedIds: Set<string>
  inviting: boolean
  inviteTargetId?: string
}>()

const emit = defineEmits<{
  (e: 'edit', row: Employee): void
  (e: 'delete', row: Employee): void
  (e: 'invite', row: Employee, isResend?: boolean): void
  (e: 'revoke', row: Employee): void
  (e: 'disable', row: Employee): void
  (e: 'profile', row: Employee): void
  (e: 'page-change', page: number): void
  (e: 'search', q: string): void
  (e: 'toggle-select', id: string): void
  (e: 'toggle-select-all'): void
}>()

const columns = [
  { key: '_select',          label: ''            },
  { key: 'employee_code',    label: 'Code'        },
  { key: 'name',             label: 'Name'        },
  { key: 'email',            label: 'Email'       },
  { key: 'department',       label: 'Department'  },
  { key: 'designation',      label: 'Designation' },
  { key: 'employment_status', label: 'Status'     },
  { key: 'account_status',   label: 'Account'     },
]

function fullName(emp: Employee | null) {
  if (!emp) return '—'
  return `${emp.first_name ?? ''} ${emp.last_name ?? ''}`.trim()
}
</script>

<template>
  <DataTable
    :columns="columns"
    :rows="employees"
    :loading="loading"
    :total="total"
    :page="page"
    :page-size="10"
    :searchable="true"
    :pagination-top="true"
    empty-text="No employees found. Create the first one!"
    @page-change="emit('page-change', $event)"
    @search="emit('search', $event)"
    @row-click="emit('profile', $event)"
  >
    <!-- Checkbox column header -->
    <template #head-_select>
      <Checkbox
        :checked="employees.length > 0 && selectedIds.size === employees.length"
        @update:checked="emit('toggle-select-all')"
        @click.stop
      />
    </template>

    <!-- Checkbox cell -->
    <template #cell-_select="{ row }">
      <Checkbox
        :checked="selectedIds.has(row.id)"
        @update:checked="emit('toggle-select', row.id)"
        @click.stop
      />
    </template>

    <!-- Custom cells -->
    <template #cell-employee_code="{ row }">
      <span
        v-if="row.employee_code"
        class="inline-block px-2 py-0.5 rounded-md bg-muted text-muted-foreground text-[10px] font-mono font-bold"
      >{{ row.employee_code }}</span>
      <span v-else class="text-muted-foreground/30 text-xs">—</span>
    </template>

    <template #cell-name="{ row }">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-[10px] font-bold text-muted-foreground shrink-0 border border-border">
          {{ (row.first_name?.[0] ?? '') + (row.last_name?.[0] ?? '') }}
        </div>
        <span class="font-semibold text-foreground">{{ fullName(row) }}</span>
      </div>
    </template>
    
    <template #cell-department="{ row }">
      <span v-if="row.department?.name" class="text-sm text-foreground">
        {{ row.department.name }}
      </span>
      <span v-else-if="row.department_id" class="text-muted-foreground/50 text-xs italic">
        ID: {{ row.department_id.slice(0, 8) }}...
      </span>
      <span v-else class="text-muted-foreground/30 text-xs">—</span>
    </template>

    <template #cell-designation="{ row }">
      <span v-if="row.designation_rel?.name" class="text-sm text-foreground">
        {{ row.designation_rel.name }}
      </span>
      <span v-else-if="row.designation" class="text-muted-foreground/50 text-xs italic">
        {{ row.designation.length > 20 ? row.designation.slice(0, 8) + '...' : row.designation }}
      </span>
      <span v-else class="text-muted-foreground/30 text-xs">—</span>
    </template>

    <template #cell-employment_status="{ row }">
      <EmployeeStatusBadge :status="row.employment_status" />
    </template>

    <template #cell-account_status="{ row }">
      <AccountStatusBadge :status="row.account_status" :expires-at="row.invite_expires_at" />
    </template>

    <!-- Actions -->
    <template #actions="{ row }">
      <div class="flex items-center justify-end space-x-1">
        <!-- Edit -->
        <Button
          variant="ghost"
          size="icon"
          @click="emit('edit', row)"
          class="h-8 w-8 rounded-md"
          title="Edit"
        >
          <Pencil class="w-4 h-4 text-muted-foreground" />
        </Button>

        <!-- Send Invite (not_registered) -->
        <Button
          v-if="row.account_status === 'not_registered'"
          variant="ghost"
          size="icon"
          @click="emit('invite', row)"
          :disabled="inviting && inviteTargetId === row.id"
          class="h-8 w-8 rounded-md text-blue-500 hover:text-blue-600 hover:bg-blue-50"
          title="Send Invite"
        >
          <Mail class="w-4 h-4" />
        </Button>

        <!-- Resend Invite (invited) -->
        <Button
          v-if="row.account_status === 'invited'"
          variant="ghost"
          size="icon"
          @click="emit('invite', row, true)"
          :disabled="inviting && inviteTargetId === row.id"
          class="h-8 w-8 rounded-md text-blue-500 hover:text-blue-600 hover:bg-blue-50"
          title="Resend Invite"
        >
          <RefreshCw class="w-4 h-4" />
        </Button>

        <!-- Revoke Invite (invited) -->
        <Button
          v-if="row.account_status === 'invited'"
          variant="ghost"
          size="icon"
          @click="emit('revoke', row)"
          class="h-8 w-8 rounded-md text-amber-500 hover:text-amber-600 hover:bg-amber-50"
          title="Revoke Invite"
        >
          <XCircle class="w-4 h-4" />
        </Button>

        <!-- Disable Account (active) -->
        <Button
          v-if="row.account_status === 'active'"
          variant="ghost"
          size="icon"
          @click="emit('disable', row)"
          class="h-8 w-8 rounded-md text-destructive hover:text-destructive hover:bg-destructive/10"
          title="Disable Account"
        >
          <ShieldOff class="w-4 h-4 text-destructive" />
        </Button>

        <!-- Delete -->
        <Button
          variant="ghost"
          size="icon"
          @click="emit('delete', row)"
          class="h-8 w-8 rounded-md text-destructive hover:text-destructive hover:bg-destructive/10"
          title="Delete"
        >
          <Trash2 class="w-4 h-4 text-destructive" />
        </Button>
      </div>
    </template>
  </DataTable>
</template>
