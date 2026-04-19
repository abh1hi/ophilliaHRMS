<script setup lang="ts">
import { ref, computed } from 'vue'
import PageHeader from '../ui/PageHeader.vue'
import { Button } from '../ui/button'
import { Download, Upload, X, FileSpreadsheet, AlertCircle, CheckCircle2, Info } from 'lucide-vue-next'
import { downloadAttendanceTemplate, uploadAttendanceCsv } from '../../services/attendance.service'
import type { UploadResult } from '../../services/attendance.service'

const selectedFile = ref<File | null>(null)
const uploading = ref(false)
const downloading = ref(false)
const result = ref<UploadResult | null>(null)
const errorMsg = ref('')

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  result.value = null
  errorMsg.value = ''
}

async function handleDownload() {
  downloading.value = true
  try { await downloadAttendanceTemplate() }
  catch (e: any) { errorMsg.value = e.message }
  finally { downloading.value = false }
}

async function handleUpload() {
  if (!selectedFile.value) return
  uploading.value = true; errorMsg.value = ''; result.value = null
  try {
    result.value = await uploadAttendanceCsv(selectedFile.value)
  } catch (e: any) { errorMsg.value = e.message }
  finally { uploading.value = false }
}

const stats = computed(() => {
  if (!result.value) return null
  return {
    total: result.value.total,
    succeeded: result.value.succeeded,
    failed: result.value.failed,
  }
})
</script>

<template>
  <div class="space-y-10 max-w-4xl">
    <PageHeader 
      title="Upload Attendance" 
      subtitle="Bulk-import attendance records via CSV synchronization" 
    />

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
      <!-- Left: Instructions & Template -->
      <div class="lg:col-span-5 space-y-6">
        <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-8 shadow-sm">
          <div class="flex items-center gap-2 mb-4">
            <Info class="w-4 h-4 text-muted-foreground" />
            <h3 class="text-xs font-bold uppercase tracking-widest">Step 1 — Preparation</h3>
          </div>
          <p class="text-[13px] text-slate-600 dark:text-slate-400 leading-relaxed mb-6">
            Ensure your data follows our standard structure. Download the template below to see required columns like 
            <code class="bg-muted px-1.5 py-0.5 rounded text-[11px] font-mono text-slate-900 border">employee_id</code> and 
            <code class="bg-muted px-1.5 py-0.5 rounded text-[11px] font-mono text-slate-900 border">clock_in</code>.
          </p>
          <Button 
            variant="outline" 
            @click="handleDownload" 
            :disabled="downloading" 
            class="w-full h-12 rounded-2xl border-slate-200 hover:bg-slate-50 text-slate-700 font-bold uppercase tracking-wider text-[11px]"
          >
            <Download class="w-4 h-4 mr-2" /> {{ downloading ? 'Preparing...' : 'Download CSV Template' }}
          </Button>
        </div>

        <div v-if="errorMsg" class="p-4 rounded-2xl bg-destructive/5 border border-destructive/20 flex items-start gap-3 animate-in fade-in slide-in-from-left-2">
          <AlertCircle class="w-4 h-4 text-destructive mt-0.5" />
          <p class="text-[11px] font-bold text-destructive uppercase tracking-tight">{{ errorMsg }}</p>
        </div>
      </div>

      <!-- Right: Upload Zone -->
      <div class="lg:col-span-7">
        <div class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-8 shadow-sm">
          <div class="flex items-center gap-2 mb-6">
            <Upload class="w-4 h-4 text-muted-foreground" />
            <h3 class="text-xs font-bold uppercase tracking-widest">Step 2 — Synchronization</h3>
          </div>

          <label class="group block w-full cursor-pointer relative overflow-hidden">
            <div 
              :class="[
                'border-2 border-dashed rounded-[22px] p-12 text-center transition-all duration-300', 
                selectedFile 
                  ? 'border-emerald-200 bg-emerald-50/30' 
                  : 'border-slate-200 hover:border-slate-400 dark:border-white/10 dark:hover:border-white/20 bg-muted/5 group-hover:bg-muted/10'
              ]"
            >
              <div v-if="!selectedFile">
                <FileSpreadsheet class="w-12 h-12 text-slate-300 mx-auto mb-4 group-hover:scale-110 transition-transform" />
                <p class="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-widest">Click to browse files</p>
                <p class="text-[11px] text-muted-foreground mt-2 font-medium">CSV format, max 10MB</p>
              </div>
              <div v-else class="animate-in zoom-in-95">
                <CheckCircle2 class="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                <p class="text-xs font-bold text-slate-900 truncate px-4">{{ selectedFile.name }}</p>
                <p class="text-[10px] text-emerald-600 font-bold uppercase tracking-tighter mt-1">{{ (selectedFile.size / 1024).toFixed(1) }} KB Ready</p>
              </div>
            </div>
            <input type="file" accept=".csv" class="hidden" @change="onFileChange" />
          </label>

          <div class="mt-8 flex items-center justify-between gap-4">
             <Button 
                v-if="selectedFile" 
                variant="ghost" 
                @click="selectedFile = null; result = null" 
                class="rounded-full px-6 h-10 text-slate-400 hover:text-destructive hover:bg-destructive/10"
              >
                <X class="w-4 h-4 mr-2" /> Clear Selection
              </Button>
              <div v-else></div>

              <Button
                @click="handleUpload"
                :disabled="!selectedFile || uploading"
                class="rounded-full px-10 h-10 bg-slate-900 text-white hover:bg-slate-800 shadow-xl shadow-slate-200 dark:shadow-none"
              >
                <Upload class="w-4 h-4 mr-2" /> {{ uploading ? 'Uploading...' : 'Upload & Synchronize' }}
              </Button>
          </div>
        </div>
      </div>
    </div>

    <!-- Results Overview -->
    <div v-if="stats" class="bg-white/40 dark:bg-slate-950/40 backdrop-blur-xl rounded-[28px] border border-white/20 dark:border-white/10 p-8 shadow-sm animate-in zoom-in-95">
      <div class="flex items-center gap-2 mb-8">
        <Info class="w-4 h-4 text-muted-foreground" />
        <h3 class="text-xs font-bold uppercase tracking-widest">Import Synchronization Summary</h3>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="p-6 rounded-3xl bg-slate-50/50 border border-dashed text-center">
          <p class="text-3xl font-black text-slate-900 tracking-tighter">{{ stats.total }}</p>
          <p class="text-[10px] font-bold uppercase tracking-widest text-muted-foreground mt-1">Total Rows</p>
        </div>
        <div class="p-6 rounded-3xl bg-emerald-50/50 border border-emerald-100 text-center">
          <p class="text-3xl font-black text-emerald-600 tracking-tighter">{{ stats.succeeded }}</p>
          <p class="text-[10px] font-bold uppercase tracking-widest text-emerald-600/70 mt-1">Direct Import</p>
        </div>
        <div class="p-6 rounded-3xl bg-rose-50/50 border border-rose-100 text-center">
          <p class="text-3xl font-black text-rose-600 tracking-tighter">{{ stats.failed }}</p>
          <p class="text-[10px] font-bold uppercase tracking-widest text-rose-600/70 mt-1">Failed Rows</p>
        </div>
      </div>

      <div v-if="result?.errors.length" class="mt-8">
        <p class="text-[11px] font-bold text-destructive uppercase tracking-widest mb-4">Conflict & Error Log</p>
        <div class="divide-y divide-white/10 overflow-hidden rounded-2xl border border-white/20">
          <div v-for="err in result.errors" :key="err.row" class="flex gap-4 p-4 text-[11px] bg-white/10 backdrop-blur-sm">
            <span class="font-bold text-slate-500 w-16 shrink-0 uppercase tracking-tighter">Row {{ err.row }}</span>
            <span class="text-rose-600 font-bold">{{ err.error }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
