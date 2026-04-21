import { apiFetchAuth, getToken } from './http'
import { API_BASE } from '../config'
import type { 
  ImportPreviewResult, ImportJobUploadResult, ImportJob 
} from './employee.types'

/** Call the preview endpoint — no DB writes, no job created. Returns per-row status. */
export async function previewImportFile(file: File): Promise<ImportPreviewResult> {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${API_BASE}/employees/bulk-import/preview`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form,
  })
  const body = await res.json()
  if (!res.ok) {
    throw new Error(body?.detail ?? `Preview failed (${res.status})`)
  }
  return body as ImportPreviewResult
}

/** Upload file to start async Celery import job. Returns job_id to poll. */
export async function uploadImportFile(
  file: File,
  dryRun: boolean,
  duplicateStrategy: 'skip' | 'update' | 'fail',
): Promise<ImportJobUploadResult> {
  const form = new FormData()
  form.append('file', file)
  form.append('dry_run', String(dryRun))
  form.append('duplicate_strategy', duplicateStrategy)
  const res = await fetch(`${API_BASE}/employees/bulk-import/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: form,
  })
  const body = await res.json()
  if (!res.ok) {
    throw new Error(body?.detail ?? `Upload failed (${res.status})`)
  }
  return body as ImportJobUploadResult
}

/** Poll the status of a running import job. */
export async function pollImportJob(jobId: string): Promise<ImportJob> {
  return apiFetchAuth<ImportJob>(`/employees/bulk-import/jobs/${jobId}`)
}

/** Get list of recent import jobs for the company (audit log). */
export async function getImportHistory(limit = 50): Promise<ImportJob[]> {
  return apiFetchAuth<ImportJob[]>(`/employees/bulk-import/jobs?limit=${limit}`)
}

/** Trigger browser download of error CSV for a completed/failed job. */
export function downloadImportErrors(jobId: string): void {
  fetch(`${API_BASE}/employees/bulk-import/jobs/${jobId}/errors.csv`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  }).then(res => res.blob()).then(blob => {
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `import_${jobId}_errors.csv`
    a.click()
    URL.revokeObjectURL(url)
  })
}
