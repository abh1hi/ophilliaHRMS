import { expect } from '@playwright/test'

/**
 * Contract validator for the employee list API response.
 * Ensures the backend response shape matches what the frontend expects.
 * Call this in real-backend integration tests to catch API drift.
 */
export function validateEmployeeListResponse(body: unknown) {
  expect(body).toMatchObject({
    total: expect.any(Number),
    employees: expect.arrayContaining([
      expect.objectContaining({
        id:                expect.any(String),
        first_name:        expect.any(String),
        last_name:         expect.any(String),
        email:             expect.any(String),
        employment_status: expect.any(String),
      }),
    ]),
  })
}

/**
 * Contract validator for a single employee object.
 */
export function validateEmployee(employee: unknown) {
  expect(employee).toMatchObject({
    id:                expect.any(String),
    first_name:        expect.any(String),
    last_name:         expect.any(String),
    email:             expect.any(String),
    employment_status: expect.any(String),
    employee_code:     expect.any(String),
  })
}

/**
 * Contract validator for the enveloped API response shape.
 */
export function validateEnvelope(body: unknown) {
  expect(body).toMatchObject({
    success: expect.any(Boolean),
    data:    expect.anything(),
    meta:    expect.anything(),
    error:   expect.anything(),
  })
}
