import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { payrollService } from '@/services/payroll.service'
import type { PayrollRun, Payslip } from '@/types/payroll.types'

export const usePayrollStore = defineStore('payroll', () => {
  const payrollRuns = ref<PayrollRun[]>([])
  const currentRun = ref<PayrollRun | null>(null)
  const payslips = ref<Payslip[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Computed
  const isLoading = computed(() => loading.value)
  const hasError = computed(() => error.value !== null)

  // Actions
  const fetchPayrollRuns = async (filters: Record<string, string> = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.getPayrollRuns(filters)
      // data may be null/undefined if the backend returns an empty envelope
      const raw = response.data
      payrollRuns.value = Array.isArray(raw) ? raw : []
    } catch (err: any) {
      error.value = err.message
      payrollRuns.value = []
    } finally {
      loading.value = false
    }
  }

  const fetchPayrollRun = async (runId: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.getPayrollRun(runId)
      currentRun.value = response.data
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createPayrollRun = async (data: {
    period_start: string
    period_end: string
    run_type?: string
  }) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.createPayrollRun(data)
      currentRun.value = response.data
      payrollRuns.value.push(response.data)
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const computePayroll = async (runId: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.computePayroll(runId)
      currentRun.value = response.data
      const index = payrollRuns.value.findIndex((r: PayrollRun) => r.id === runId)
      if (index !== -1) {
        payrollRuns.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const approvePayroll = async (runId: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.approvePayroll(runId)
      currentRun.value = response.data
      const index = payrollRuns.value.findIndex((r: PayrollRun) => r.id === runId)
      if (index !== -1) {
        payrollRuns.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const rejectPayroll = async (runId: string, reason: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.rejectPayroll(runId, reason)
      currentRun.value = response.data
      const index = payrollRuns.value.findIndex((r: PayrollRun) => r.id === runId)
      if (index !== -1) {
        payrollRuns.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const processPayroll = async (runId: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.processPayroll(runId)
      currentRun.value = response.data
      const index = payrollRuns.value.findIndex((r: PayrollRun) => r.id === runId)
      if (index !== -1) {
        payrollRuns.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const markPayrollPaid = async (runId: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.markPayrollPaid(runId)
      currentRun.value = response.data
      const index = payrollRuns.value.findIndex((r: PayrollRun) => r.id === runId)
      if (index !== -1) {
        payrollRuns.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const lockPayroll = async (runId: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.lockPayroll(runId)
      currentRun.value = response.data
      const index = payrollRuns.value.findIndex((r: PayrollRun) => r.id === runId)
      if (index !== -1) {
        payrollRuns.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const retryPayroll = async (runId: string) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.retryPayroll(runId)
      currentRun.value = response.data
      const index = payrollRuns.value.findIndex((r: PayrollRun) => r.id === runId)
      if (index !== -1) {
        payrollRuns.value[index] = response.data
      }
      return response.data
    } catch (err: any) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const fetchPayslips = async (runId: string, filters: Record<string, string> = {}) => {
    loading.value = true
    error.value = null
    try {
      const response = await payrollService.getPayslips(runId, filters)
      const raw = response.data
      payslips.value = Array.isArray(raw) ? raw : []
      return payslips.value
    } catch (err: any) {
      error.value = err.message
      payslips.value = []
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    payrollRuns,
    currentRun,
    payslips,
    loading,
    error,
    isLoading,
    hasError,
    fetchPayrollRuns,
    fetchPayrollRun,
    createPayrollRun,
    computePayroll,
    approvePayroll,
    rejectPayroll,
    processPayroll,
    markPayrollPaid,
    lockPayroll,
    retryPayroll,
    fetchPayslips,
    clearError,
  }
})
