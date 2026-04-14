/**
 * Fire-and-forget analytics event via sendBeacon.
 * Survives page unload. Fails silently if endpoint doesn't exist yet.
 * Set ANALYTICS_ENABLED to true once /api/v1/analytics/events is live.
 */
const ANALYTICS_ENABLED = false

export function trackEvent(name: string, props: Record<string, unknown> = {}): void {
  if (!ANALYTICS_ENABLED) return
  try {
    const payload = JSON.stringify({
      event: name,
      timestamp: new Date().toISOString(),
      company_id: localStorage.getItem('selected_company_id'),
      ...props,
    })
    navigator.sendBeacon(
      '/api/v1/analytics/events',
      new Blob([payload], { type: 'application/json' })
    )
  } catch {
    // sendBeacon not supported or endpoint missing — ignore silently
  }
}
