import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { api } from '@/lib/api'

describe('api client', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock)
    window.history.replaceState({}, '', '/data-hub')
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.unstubAllGlobals()
  })

  it('builds relative API requests against the current origin', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await api.listCompanies()

    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(fetchMock.mock.calls[0]?.[0]).toBe(`${window.location.origin}/api/v1/org/companies`)
  })

  it('appends query parameters for list endpoints', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify([]), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await api.listCandidates({ companyId: 'company-1', limit: 20 })

    const requestUrl = new URL(String(fetchMock.mock.calls[0]?.[0]))
    expect(requestUrl.pathname).toBe('/api/v1/candidates')
    expect(requestUrl.searchParams.get('companyId')).toBe('company-1')
    expect(requestUrl.searchParams.get('limit')).toBe('20')
  })
})
