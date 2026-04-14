import { apiFetchAuth } from './http'

// ─── Types ────────────────────────────────────────────────────────────────────
export interface OnboardingStep {
  step_key: string
  label: string
  order: number
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'SKIPPED' | 'FAILED'
  completed_at: string | null
}

export interface OnboardingStatus {
  company_id: string
  status: string
  steps: OnboardingStep[]
  progress_percent: number
  started_at: string | null
  completed_at: string | null
}

export interface OnboardingTemplate {
  id: string
  category: string
  region: string
  name: string
  template_json: string
}

export interface SagaStepResult {
  step: string
  status: string
  error?: string
}

export interface ApplyTemplateResult {
  status: 'COMPLETED' | 'PARTIAL' | 'ALREADY_APPLIED' | 'FAILED'
  log_id?: string
  message?: string
  failed_step?: string
  error?: string
  compensation_status?: string
  saga_steps?: SagaStepResult[]
}

// ─── API ─────────────────────────────────────────────────────────────────────
export async function getOnboardingStatus(): Promise<OnboardingStatus> {
  return apiFetchAuth<OnboardingStatus>('/onboarding/status')
}

export async function completeStep(step_key: string, skipped = false): Promise<OnboardingStatus> {
  return apiFetchAuth<OnboardingStatus>('/onboarding/complete-step', {
    method: 'POST',
    body: JSON.stringify({ step_key, skipped }),
  })
}

export async function completeWizard(): Promise<OnboardingStatus> {
  return apiFetchAuth<OnboardingStatus>('/onboarding/complete-wizard', {
    method: 'POST',
  })
}

export async function listTemplates(region?: string): Promise<OnboardingTemplate[]> {
  const q = region ? `?region=${region}` : ''
  return apiFetchAuth<OnboardingTemplate[]>(`/onboarding/templates${q}`)
}

export async function applyTemplate(region: string): Promise<ApplyTemplateResult> {
  return apiFetchAuth<ApplyTemplateResult>('/onboarding/apply-template', {
    method: 'POST',
    body: JSON.stringify({ region }),
  })
}
