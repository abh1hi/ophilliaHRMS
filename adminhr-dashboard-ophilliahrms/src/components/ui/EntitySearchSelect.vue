<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { Search, X, ChevronDown } from 'lucide-vue-next'
import { listEmployees } from '@/services/employee.service'

type Entity = 'employee'

const props = withDefaults(defineProps<{
  modelValue: string | string[]
  label: string
  entity?: Entity
  multiple?: boolean
  placeholder?: string
  required?: boolean
}>(), {
  entity: 'employee',
  multiple: false,
  placeholder: 'Search...',
})

const emit = defineEmits<{
  (e: 'update:modelValue', val: string | string[]): void
}>()

interface Option {
  value: string
  label: string
  sub?: string
}

const query = ref('')
const options = ref<Option[]>([])
const loading = ref(false)
const open = ref(false)
const containerRef = ref<HTMLElement | null>(null)
const activeIdx = ref(-1)

// For multiple mode: array of selected items with label cached
const selectedItems = ref<Option[]>([])

let debounceTimer: ReturnType<typeof setTimeout>

async function search(q: string) {
  loading.value = true
  try {
    if (props.entity === 'employee') {
      const res = await listEmployees({ search: q || undefined, page: 1, page_size: 10 })
      options.value = res.data.map(e => ({
        value: e.id,
        label: `${e.first_name} ${e.last_name}`,
        sub: `${e.employee_code || ''} • ${e.department || ''}`.replace(/^•\s*|•\s*$/, '').trim(),
      }))
    }
  } catch {
    options.value = []
  } finally {
    loading.value = false
  }
}

watch(query, (q) => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => search(q), 300)
})

function onFocus() {
  open.value = true
  if (!options.value.length) search('')
}

function select(opt: Option) {
  if (props.multiple) {
    const vals = Array.isArray(props.modelValue) ? [...props.modelValue] : []
    if (!vals.includes(opt.value)) {
      vals.push(opt.value)
      selectedItems.value = [...selectedItems.value, opt]
      emit('update:modelValue', vals)
    }
    query.value = ''
  } else {
    emit('update:modelValue', opt.value)
    query.value = opt.label
    open.value = false
  }
}

function removeItem(val: string) {
  const vals = (Array.isArray(props.modelValue) ? [...props.modelValue] : []).filter(v => v !== val)
  selectedItems.value = selectedItems.value.filter(i => i.value !== val)
  emit('update:modelValue', vals)
}

function clearSingle() {
  emit('update:modelValue', '')
  query.value = ''
  open.value = false
}

function onKeydown(e: KeyboardEvent) {
  if (!open.value) return
  if (e.key === 'ArrowDown') { e.preventDefault(); activeIdx.value = Math.min(activeIdx.value + 1, options.value.length - 1) }
  if (e.key === 'ArrowUp') { e.preventDefault(); activeIdx.value = Math.max(activeIdx.value - 1, 0) }
  if (e.key === 'Enter' && activeIdx.value >= 0) { e.preventDefault(); select(options.value[activeIdx.value]) }
  if (e.key === 'Escape') { open.value = false }
}

function onClickOutside(e: MouseEvent) {
  if (containerRef.value && !containerRef.value.contains(e.target as Node)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))

// Sync single-value display label on mount/change
watch(() => props.modelValue, async (val) => {
  if (!props.multiple && typeof val === 'string' && val && !query.value) {
    const res = await listEmployees({ search: val, page: 1, page_size: 1 })
    const match = res.employees.find(e => e.id === val)
    if (match) query.value = `${match.first_name} ${match.last_name}`
  }
}, { immediate: true })
</script>

<template>
  <div class="space-y-2" ref="containerRef">
    <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
      {{ label }}<span v-if="required" class="text-destructive ml-0.5">*</span>
    </label>

    <!-- Chips for multiple mode -->
    <div v-if="multiple && selectedItems.length" class="flex flex-wrap gap-1.5 mb-1">
      <span
        v-for="item in selectedItems"
        :key="item.value"
        class="inline-flex items-center gap-1 pl-2.5 pr-1.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-xs font-medium text-slate-700"
      >
        {{ item.label }}
        <button type="button" @click="removeItem(item.value)" class="w-4 h-4 rounded-full hover:bg-slate-300 flex items-center justify-center transition-colors">
          <X class="w-2.5 h-2.5" />
        </button>
      </span>
    </div>

    <div class="relative">
      <div class="relative flex items-center">
        <Search class="absolute left-3 w-4 h-4 text-slate-400 pointer-events-none" />
        <input
          type="text"
          v-model="query"
          :placeholder="placeholder"
          @focus="onFocus"
          @keydown="onKeydown"
          class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pl-9 pr-8"
        />
        <button
          v-if="!multiple && modelValue"
          type="button"
          @click="clearSingle"
          class="absolute right-2 w-5 h-5 rounded-full hover:bg-slate-100 flex items-center justify-center transition-colors"
        >
          <X class="w-3 h-3 text-slate-400" />
        </button>
        <ChevronDown v-else class="absolute right-3 w-4 h-4 text-slate-400 pointer-events-none" />
      </div>

      <!-- Dropdown -->
      <div
        v-if="open"
        class="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden"
      >
        <div v-if="loading" class="flex items-center gap-2 px-4 py-3 text-xs text-slate-500">
          <div class="w-3 h-3 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin"></div>
          Searching...
        </div>
        <div v-else-if="!options.length" class="px-4 py-3 text-xs text-slate-400">No results found</div>
        <ul v-else class="max-h-52 overflow-y-auto">
          <li
            v-for="(opt, idx) in options"
            :key="opt.value"
            @mousedown.prevent="select(opt)"
            :class="['flex flex-col px-4 py-2.5 cursor-pointer hover:bg-slate-50 transition-colors text-sm', idx === activeIdx ? 'bg-slate-50' : '']"
          >
            <span class="font-medium text-slate-900">{{ opt.label }}</span>
            <span v-if="opt.sub" class="text-[11px] text-slate-400 mt-0.5">{{ opt.sub }}</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
