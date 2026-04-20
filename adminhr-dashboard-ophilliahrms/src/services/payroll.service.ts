import { apiFetch } from './api'
import type { PayrollRun, Payslip } from '@/types/payroll.types'

export const payrollService = {
  // Payroll Runs
  getPayrollRuns: (params: Record<string, string> = {}) => {
    const query = new URLSearchParams(params).toString()
    return apiFetch<PayrollRun[]>(`/payroll/runs?${query}`)
  },

  getPayrollRun: (runId: string) => {
    return apiFetch<PayrollRun>(`/payroll/runs/${runId}`)
  },

  createPayrollRun: (data: { period_start: string; period_end: string; run_type?: string }) => {
    return apiFetch<PayrollRun>('/payroll/runs', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },

  // Lifecycle Actions
  computePayroll: (runId: string) => {
    return apiFetch<PayrollRun>(`/payroll/runs/${runId}/compute`, {
      method: 'POST',
    })
  },

  approvePayroll: (runId: string) => {
    return apiFetch<PayrollRun>(`/payroll/runs/${runId}/approve`, {
      method: 'POST',
    })
  },

  rejectPayroll: (runId: string, reason: string) => {
    return apiFetch<PayrollRun>(`/payroll/runs/${runId}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    })
  },

  processPayroll: (runId: string) => {
    return apiFetch<PayrollRun>(`/payroll/runs/${runId}/process`, {
      method: 'POST',
    })
  },

  markPayrollPaid: (runId: string) => {
    return apiFetch<PayrollRun>(`/payroll/runs/${runId}/mark-paid`, {
      method: 'POST',
    })
  },

  lockPayroll: (runId: string) => {
    return apiFetch<PayrollRun>(`/payroll/runs/${runId}/lock`, {
      method: 'POST',
    })
  },

  retryPayroll: (runId: string) => {
    return apiFetch<PayrollRun>(`/payroll/runs/${runId}/retry`, {
      method: 'POST',
    })
  },

  // Payslips
  getPayslips: (runId: string, params: Record<string, string> = {}) => {
    const query = new URLSearchParams(params).toString()
    return apiFetch<Payslip[]>(`/payroll/runs/${runId}/payslips?${query}`)
  },

  getPayslip: (runId: string, payslipId: string) => {
    return apiFetch<Payslip>(`/payroll/runs/${runId}/payslips/${payslipId}`)
  },

  // Reports & Exports
  downloadECR: (runId: string) => {
    return fetch(`/api/payroll/runs/${runId}/ecr-file`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    }).then(res => res.blob())
  },

  downloadBankAdvice: (runId: string) => {
    return fetch(`/api/payroll/runs/${runId}/bank-advice`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    }).then(res => res.blob())
  },

  downloadForm16: (employeeId: string, financialYear: number) => {
    return fetch(`/api/payroll/employees/${employeeId}/form16?fy=${financialYear}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    }).then(res => res.blob())
  },

  getESICReturn: (runId: string) => {
    return apiFetch<any>(`/payroll/runs/${runId}/esic-return`)
  },

  // Salary Structures & Tax Profiles
  getSalaryStructures: (params: Record<string, string> = {}) => {
    const query = new URLSearchParams(params).toString()
    return apiFetch<any[]>(`/payroll/salary-structures?${query}`)
  },

  createSalaryStructure: (data: any) =>
    apiFetch<any>('/payroll/salary-structures', { method: 'POST', body: JSON.stringify(data) }),

  updateSalaryStructure: (id: string, data: any) =>
    apiFetch<any>(`/payroll/salary-structures/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  deleteSalaryStructure: (id: string) =>
    apiFetch<any>(`/payroll/salary-structures/${id}`, { method: 'DELETE' }),

  getTaxProfile: (employeeId: string, financialYear: number) => {
    return apiFetch<any>(`/payroll/tax-profiles/${employeeId}?fy=${financialYear}`)
  },

  createTaxProfile: (data: any) =>
    apiFetch<any>('/payroll/tax-profiles', { method: 'POST', body: JSON.stringify(data) }),

  updateTaxProfile: (employeeId: string, financialYear: number, data: any) => {
    return apiFetch<any>(`/payroll/tax-profiles/${employeeId}?fy=${financialYear}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    })
  },
}
