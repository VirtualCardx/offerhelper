import { describe, expect, it } from 'vitest'

import { resolveCompanyScopeSelection, resolveScopedId } from '@/lib/context-sync'

describe('context sync helpers', () => {
  it('keeps preferred id when it exists in scope', () => {
    expect(resolveScopedId([{ id: 'a' }, { id: 'b' }], 'b')).toBe('b')
  })

  it('falls back to first scoped id when preferred value is missing', () => {
    expect(resolveScopedId([{ id: 'a' }, { id: 'b' }], 'missing')).toBe('a')
  })

  it('resolves department, position, and strategy together', () => {
    expect(
      resolveCompanyScopeSelection({
        departments: [{ id: 'dep-1' }, { id: 'dep-2' }],
        positions: [{ id: 'pos-1' }, { id: 'pos-2' }],
        strategies: [{ id: 'st-1' }, { id: 'st-2' }],
        preferredDepartmentId: 'dep-2',
        preferredPositionId: 'missing',
        preferredStrategyId: 'st-2',
      }),
    ).toEqual({
      departmentId: 'dep-2',
      positionId: 'pos-1',
      strategyId: 'st-2',
    })
  })
})
