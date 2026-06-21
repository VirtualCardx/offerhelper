import { describe, expect, it } from 'vitest'

import { defaultDemoContext } from '@/lib/demo-defaults'
import { useAppStore } from '@/store/useAppStore'

describe('useAppStore', () => {
  it('resets persisted demo context to defaults', () => {
    useAppStore.setState({
      demoContext: {
        ...defaultDemoContext,
        companyId: 'company-1',
        departmentId: 'department-1',
        positionId: 'position-1',
        strategyId: 'strategy-1',
        city: 'Beijing',
      },
    })

    useAppStore.getState().resetDemoContext()

    expect(useAppStore.getState().demoContext).toEqual(defaultDemoContext)
  })
})
