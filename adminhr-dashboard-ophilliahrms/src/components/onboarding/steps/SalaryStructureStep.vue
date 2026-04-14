<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { BanknoteIcon } from 'lucide-vue-next'
import { apiFetchData } from '../../../services/http'
import { handleApiError } from '../../../utils/handleApiError'

const DRAFT_KEY = 'onboarding_draft_salary_structure'

const emit = defineEmits<{ completed: []; skipped: [] }>()
const props = defineProps<{ readonly?: boolean }>()

const saving = ref(false)
const errorMsg = ref('')
const form = reactive({
  name: 'Standard Salary Structure',
  basic_pct: 50,
  hra_pct: 20,
  allowances_pct: 15,
  pf_pct: 12,
  esi_pct: 1.75,
  professional_tax: 200,
})

// Live preview (for a sample CTC of ₹50,000)
const SAMPLE_CTC = 50000
const preview = computed(() => {
  const basic = (SAMPLE_CTC * form.basic_pct) / 100
  const hra = (SAMPLE_CTC * form.hra_pct) / 100
  const allowances = (SAMPLE_CTC * form.allowances_pct) / 100
  const pf = (SAMPLE_CTC * form.pf_pct) / 100
  const esi = (SAMPLE_CTC * form.esi_pct) / 100
  const pt = form.professional_tax
  const gross = basic + hra + allowances
  const deductions = pf + esi + pt
  const net = gross - deductions
  return { basic, hra, allowances, pf, esi, pt, gross, deductions, net }
})

watch(form, val => {
  localStorage.setItem(DRAFT_KEY, JSON.stringify(val))
}, { deep: true })

onMounted(() => {
  const saved = localStorage.getItem(DRAFT_KEY)
  if (saved) {
    try { Object.assign(form, JSON.parse(saved)) } catch {}
  }
})

function fmt(n: number) {
  return '₹' + Math.round(n).toLocaleString('en-IN')
}

async function submit() {
  if (saving.value) return
  if (!form.name.trim()) { errorMsg.value = 'Structure name is required'; return }

  saving.value = true
  errorMsg.value = ''
  try {
    await apiFetchData('/salary-structures', {
      method: 'POST',
      body: JSON.stringify({
        name: form.name.trim(),
        basic_pct: form.basic_pct,
        hra_pct: form.hra_pct,
        allowances_pct: form.allowances_pct,
        pf_pct: form.pf_pct,
        esi_pct: form.esi_pct,
        professional_tax: form.professional_tax,
      }),
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
  <div class="max-w-2xl">
    <div class="flex items-center space-x-3 mb-8">
      <div class="w-11 h-11 bg-slate-100 rounded-[14px] flex items-center justify-center">
        <BanknoteIcon class="w-5 h-5 text-slate-600" />
      </div>
      <div>
        <h2 class="text-xl font-bold text-slate-900 leading-tight">Configure salary structure</h2>
        <p class="text-sm text-slate-400 font-medium mt-0.5">Set salary components and statutory deductions</p>
      </div>
    </div>

    <!-- Read-only for HR -->
    <div v-if="props.readonly" class="p-4 bg-slate-50 border border-slate-200 rounded-[14px] text-sm text-slate-500 font-medium mb-6">
      Salary structure can only be configured by an admin.
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Form -->
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-semibold text-slate-700 mb-1.5">Structure Name <span class="text-rose-500">*</span></label>
          <input
            v-model="form.name"
            type="text"
            class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[12px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-4 py-3 outline-none transition-all"
          />
        </div>

        <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide pt-1">Earnings (%)</p>

        <div class="grid grid-cols-3 gap-3">
          <div v-for="field in [
            { key: 'basic_pct', label: 'Basic' },
            { key: 'hra_pct', label: 'HRA' },
            { key: 'allowances_pct', label: 'Allowances' },
          ]" :key="field.key">
            <label class="block text-xs font-semibold text-slate-600 mb-1">{{ field.label }} %</label>
            <input
              v-model.number="(form as any)[field.key]"
              type="number"
              min="0"
              max="100"
              step="0.5"
              class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[10px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-3 py-2.5 outline-none transition-all text-center"
            />
          </div>
        </div>

        <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide pt-1">Deductions</p>

        <div class="grid grid-cols-3 gap-3">
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">PF %</label>
            <input v-model.number="form.pf_pct" type="number" min="0" max="100" step="0.5"
              class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[10px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-3 py-2.5 outline-none transition-all text-center" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">ESI %</label>
            <input v-model.number="form.esi_pct" type="number" min="0" max="100" step="0.25"
              class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[10px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-3 py-2.5 outline-none transition-all text-center" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-600 mb-1">Prof. Tax ₹</label>
            <input v-model.number="form.professional_tax" type="number" min="0"
              class="w-full bg-white border border-slate-200 text-slate-900 text-sm rounded-[10px] focus:ring-2 focus:ring-slate-900/10 focus:border-slate-400 px-3 py-2.5 outline-none transition-all text-center" />
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
            <span>{{ saving ? 'Saving...' : 'Save Structure' }}</span>
          </button>
          <button @click="skip" :disabled="saving" class="px-5 py-3 text-slate-400 hover:text-slate-600 text-sm font-medium transition-colors">
            Skip for now
          </button>
        </div>
      </div>

      <!-- Live Preview -->
      <div class="bg-slate-50 border border-slate-200 rounded-[16px] p-5 h-fit">
        <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-4">Preview (₹50,000 CTC)</p>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between"><span class="text-slate-500">Basic</span><span class="font-semibold text-slate-800">{{ fmt(preview.basic) }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">HRA</span><span class="font-semibold text-slate-800">{{ fmt(preview.hra) }}</span></div>
          <div class="flex justify-between"><span class="text-slate-500">Allowances</span><span class="font-semibold text-slate-800">{{ fmt(preview.allowances) }}</span></div>
          <div class="border-t border-slate-200 pt-2 flex justify-between font-semibold">
            <span class="text-slate-700">Gross</span>
            <span class="text-slate-900">{{ fmt(preview.gross) }}</span>
          </div>
          <div class="flex justify-between text-rose-600"><span>PF</span><span>- {{ fmt(preview.pf) }}</span></div>
          <div class="flex justify-between text-rose-600"><span>ESI</span><span>- {{ fmt(preview.esi) }}</span></div>
          <div class="flex justify-between text-rose-600"><span>Prof. Tax</span><span>- {{ fmt(preview.pt) }}</span></div>
          <div class="border-t border-slate-200 pt-2 flex justify-between font-bold text-base">
            <span class="text-slate-900">Net Pay</span>
            <span class="text-emerald-600">{{ fmt(preview.net) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
