// ─── Centralized App Configuration ────────────────────────────────────────────
// Single source of truth for all environment-driven values.
// All services import from here — never read import.meta.env directly elsewhere.

/** API base path (e.g. '/api/v1') */
export const API_BASE = import.meta.env.VITE_API_BASE_PATH || '/api/v1'

/** Full gateway URL — used only by vite.config.ts proxy; empty in production */
export const API_GATEWAY_URL = import.meta.env.VITE_API_GATEWAY_URL || 'http://localhost:80'

/** App identity */
export const APP_NAME       = import.meta.env.VITE_APP_NAME    || 'Ophillia HRMS Admin'
export const APP_VERSION    = import.meta.env.VITE_APP_VERSION || '1.0.0'

/** Runtime environment helpers */
export const IS_DEV  = import.meta.env.DEV
export const IS_PROD = import.meta.env.PROD
