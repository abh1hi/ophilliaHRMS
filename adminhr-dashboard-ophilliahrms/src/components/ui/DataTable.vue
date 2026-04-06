<script setup lang="ts" generic="T extends Record<string, any>">
import { ref, computed } from 'vue'
import { SearchIcon, ChevronLeftIcon, ChevronRightIcon } from 'lucide-vue-next'

const props = defineProps<{
  columns: { key: string; label: string; class?: string }[]
  rows: T[]
  loading?: boolean
  total?: number
  page?: number
  pageSize?: number
  searchable?: boolean
  emptyText?: string
}>()

const emit = defineEmits<{
  (e: 'page-change', page: number): void
  (e: 'search', query: string): void
}>()

const searchQuery = ref('')
let searchTimeout: ReturnType<typeof setTimeout>

function onSearch() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => emit('search', searchQuery.value), 350)
}

const totalPages = computed(() => Math.ceil((props.total ?? props.rows?.length ?? 0) / (props.pageSize ?? 20)))
</script>

<template>
  <div class="space-y-4">
    <!-- Search Bar -->
    <div v-if="searchable" class="relative">
      <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400">
        <SearchIcon class="w-4 h-4" />
      </div>
      <input
        v-model="searchQuery"
        @input="onSearch"
        type="search"
        placeholder="Search..."
        autocomplete="off"
        class="w-full max-w-sm bg-white/60 border border-slate-200/60 text-slate-900 text-sm rounded-[14px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 pl-10 pr-4 py-2.5 outline-none transition-all"
      />
    </div>

    <!-- Table -->
    <div class="overflow-x-auto rounded-[18px] border border-slate-200/60 bg-white/50 backdrop-blur">
      <table class="w-full text-sm text-left">
        <thead class="border-b border-slate-200/60 bg-white/40">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              :class="['px-5 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider', col.class]"
            >
              {{ col.label }}
            </th>
            <th class="px-5 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <!-- Loading -->
          <tr v-if="loading">
            <td :colspan="columns.length + 1" class="px-5 py-12 text-center text-slate-400">
              <div class="flex items-center justify-center space-x-2">
                <div class="w-4 h-4 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin"></div>
                <span>Loading...</span>
              </div>
            </td>
          </tr>
          <!-- Empty -->
          <tr v-else-if="!rows?.length">
            <td :colspan="columns.length + 1" class="px-5 py-12 text-center text-slate-400">
              {{ emptyText || 'No records found.' }}
            </td>
          </tr>
          <!-- Data Rows -->
          <tr
            v-else
            v-for="(row, idx) in (rows ?? [])"
            :key="row.id ?? idx"
            class="border-b border-slate-100/60 hover:bg-white/60 transition-colors group"
          >
            <td
              v-for="col in columns"
              :key="col.key"
              :class="['px-5 py-4 text-slate-700', col.class]"
            >
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                {{ row[col.key] ?? '—' }}
              </slot>
            </td>
            <td class="px-5 py-4 text-right">
              <slot name="actions" :row="row" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between pt-2">
      <span class="text-sm text-slate-500">
        Page {{ page ?? 1 }} of {{ totalPages }}
      </span>
      <div class="flex items-center space-x-2">
        <button
          @click="emit('page-change', (page ?? 1) - 1)"
          :disabled="(page ?? 1) <= 1"
          class="p-2 rounded-[10px] border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronLeftIcon class="w-4 h-4 text-slate-600" />
        </button>
        <button
          @click="emit('page-change', (page ?? 1) + 1)"
          :disabled="(page ?? 1) >= totalPages"
          class="p-2 rounded-[10px] border border-slate-200 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          <ChevronRightIcon class="w-4 h-4 text-slate-600" />
        </button>
      </div>
    </div>
  </div>
</template>
