<script setup lang="ts">
import FormSelect from '../ui/FormSelect.vue'

const props = defineProps<{
  statusFilter: string
  accountFilter: string
}>()

const emit = defineEmits<{
  (e: 'update:statusFilter', val: string): void
  (e: 'update:accountFilter', val: string): void
}>()

const statusOptions = [
  { value: '',           label: 'All Statuses'  },
  { value: 'active',     label: 'Active'        },
  { value: 'inactive',   label: 'Inactive'      },
  { value: 'terminated', label: 'Terminated'    },
]

const accountStatusOptions = [
  { value: '',               label: 'All Accounts'   },
  { value: 'not_registered', label: 'Not Registered' },
  { value: 'invited',        label: 'Invite Sent'    },
  { value: 'active',         label: 'Active'         },
  { value: 'suspended',      label: 'Suspended'      },
]
</script>

<template>
  <div class="flex items-center gap-4 flex-wrap">
    <div class="w-52">
      <FormSelect
        label=""
        :modelValue="statusFilter"
        :options="statusOptions"
        @update:modelValue="emit('update:statusFilter', $event)"
      />
    </div>
    <div class="w-52">
      <FormSelect
        label=""
        :modelValue="accountFilter"
        :options="accountStatusOptions"
        @update:modelValue="emit('update:accountFilter', $event)"
      />
    </div>
  </div>
</template>
