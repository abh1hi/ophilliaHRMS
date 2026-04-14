export function handleApiError(err: unknown): string {
  if (err instanceof Error) return err.message
  if (typeof err === 'object' && err !== null) {
    if ('detail' in err) return String((err as any).detail)
    if ('message' in err) return String((err as any).message)
  }
  return 'An unexpected error occurred. Please try again.'
}
