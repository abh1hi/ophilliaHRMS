<script setup lang="ts" generic="T extends Record<string, any>">
import { ref, computed } from 'vue'
import { Search, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { Input } from './input'
import { Button } from './button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from './table'
import { ScrollArea } from './scroll-area'

const props = defineProps<{
  columns: { key: string; label: string; class?: string }[]
  rows: T[]
  loading?: boolean
  total?: number
  page?: number
  pageSize?: number
  searchable?: boolean
  emptyText?: string
  paginationTop?: boolean
}>()

const emit = defineEmits<{
  (e: 'page-change', page: number): void
  (e: 'search', query: string): void
  (e: 'row-click', row: T): void
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
    <!-- Top controls: search + optional top pagination -->
    <div class="flex items-center justify-between gap-4 flex-wrap">
      <!-- Search -->
      <div v-if="searchable" class="relative flex-1 max-w-sm">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          v-model="searchQuery"
          @input="onSearch"
          type="search"
          placeholder="Search..."
          class="pl-9 h-10"
        />
      </div>
      <div v-else class="flex-1" />

      <!-- Top Pagination -->
      <div v-if="paginationTop && totalPages > 1" class="flex items-center gap-2 shrink-0">
        <span class="text-sm text-muted-foreground whitespace-nowrap">
          Page {{ page ?? 1 }} of {{ totalPages }}
        </span>
        <Button
          variant="outline"
          size="icon"
          :disabled="(page ?? 1) <= 1"
          @click="emit('page-change', (page ?? 1) - 1)"
          class="h-8 w-8"
        >
          <ChevronLeft class="w-4 h-4" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          :disabled="(page ?? 1) >= totalPages"
          @click="emit('page-change', (page ?? 1) + 1)"
          class="h-8 w-8"
        >
          <ChevronRight class="w-4 h-4" />
        </Button>
      </div>
    </div>

    <!-- Table Container with Responsive Scroll -->
    <ScrollArea class="w-full rounded-md border border-border">
      <div class="min-w-[800px] w-full"> <!-- Minimum width to avoid squished columns on mobile -->
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead
                v-for="col in columns"
                :key="col.key"
                :class="col.class"
              >
                <slot :name="`head-${col.key}`">{{ col.label }}</slot>
              </TableHead>
              <TableHead class="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <!-- Loading -->
            <TableRow v-if="loading">
              <TableCell :colspan="columns.length + 1" class="h-32 text-center text-muted-foreground">
                <div class="flex items-center justify-center space-x-2">
                  <div class="w-4 h-4 border-2 border-muted border-t-foreground rounded-full animate-spin"></div>
                  <span>Loading...</span>
                </div>
              </TableCell>
            </TableRow>
            <!-- Empty -->
            <TableRow v-else-if="!rows?.length">
              <TableCell :colspan="columns.length + 1" class="h-32 text-center text-muted-foreground">
                {{ emptyText || 'No records found.' }}
              </TableCell>
            </TableRow>
            <!-- Data Rows -->
            <TableRow
              v-else
              v-for="(row, idx) in (rows ?? [])"
              :key="row.id ?? idx"
              class="cursor-pointer group hover:bg-muted/50 transition-colors"
              @click="emit('row-click', row)"
            >
              <TableCell
                v-for="col in columns"
                :key="col.key"
                :class="col.class"
              >
                <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                  {{ row[col.key] ?? '—' }}
                </slot>
              </TableCell>
              <TableCell class="text-right" @click.stop>
                <slot name="actions" :row="row" />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </ScrollArea>

    <!-- Bottom Pagination -->
    <div v-if="totalPages > 1" class="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
      <span class="text-sm text-muted-foreground">
        Page {{ page ?? 1 }} of {{ totalPages }}
        <span class="text-muted-foreground/60 ml-1">({{ total }} total)</span>
      </span>
      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          :disabled="(page ?? 1) <= 1"
          @click="emit('page-change', (page ?? 1) - 1)"
          class="gap-1.5"
        >
          <ChevronLeft class="w-4 h-4" />
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          :disabled="(page ?? 1) >= totalPages"
          @click="emit('page-change', (page ?? 1) + 1)"
          class="gap-1.5"
        >
          Next
          <ChevronRight class="w-4 h-4" />
        </Button>
      </div>
    </div>
  </div>
</template>
