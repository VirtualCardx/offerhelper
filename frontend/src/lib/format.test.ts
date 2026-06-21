import { describe, expect, it } from 'vitest'

import { formatCurrency, formatDateTime, formatPercent } from '@/lib/format'

describe('format helpers', () => {
  it('formats currency values', () => {
    expect(formatCurrency('38000')).toContain('38,000')
  })

  it('formats percentages from decimal strings', () => {
    expect(formatPercent('0.85')).toBe('85.0%')
  })

  it('formats datetime strings', () => {
    expect(formatDateTime('2026-06-20T10:30:00+00:00')).not.toBe('--')
  })
})
