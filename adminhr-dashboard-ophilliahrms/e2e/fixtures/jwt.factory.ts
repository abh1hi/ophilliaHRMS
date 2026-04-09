/**
 * JWT factory for e2e tests.
 *
 * The router guard decodes JWTs client-side via atob() with no cryptographic
 * verification, so we can forge plausible-looking tokens that the guard accepts.
 * This lets tests set up auth state in microseconds without a real backend.
 */

export function buildMockJwt(claims: {
  sub: string
  role: 'super_admin' | 'admin' | 'hr' | 'employee'
  email: string
  company_id?: string
  /** Seconds since epoch. Defaults to 1 hour from now. */
  exp?: number
}): string {
  const b64url = (obj: object) =>
    btoa(JSON.stringify(obj))
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '')

  const header  = b64url({ alg: 'HS256', typ: 'JWT' })
  const payload = b64url({
    sub:        claims.sub,
    role:       claims.role,
    email:      claims.email,
    company_id: claims.company_id ?? 'test-co-1',
    exp:        claims.exp ?? Math.floor(Date.now() / 1000) + 3600,
  })

  // Dummy signature — not verified client-side
  return `${header}.${payload}.fakesignatureforplaywrighttests`
}

export const mockTokens = {
  admin: buildMockJwt({
    sub: 'u-admin-1', role: 'admin', email: 'admin@test.com', company_id: 'co-1',
  }),
  hr: buildMockJwt({
    sub: 'u-hr-1', role: 'hr', email: 'hr@test.com', company_id: 'co-1',
  }),
  employee: buildMockJwt({
    sub: 'u-emp-1', role: 'employee', email: 'emp@test.com', company_id: 'co-1',
  }),
  superAdmin: buildMockJwt({
    sub: 'u-sa-1', role: 'super_admin', email: 'sa@test.com',
  }),
  expired: buildMockJwt({
    sub: 'u-exp-1', role: 'admin', email: 'exp@test.com', company_id: 'co-1',
    exp: Math.floor(Date.now() / 1000) - 60, // already expired
  }),
}
