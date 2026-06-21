import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import { defaultDemoContext } from '@/lib/demo-defaults'
import type { DemoContext } from '@/types/api'

type AppState = {
  demoContext: DemoContext
  lastCandidateId: string | null
  lastOfferId: string | null
  lastTaskId: string | null
  setDemoContext: (patch: Partial<DemoContext>) => void
  resetDemoContext: () => void
  setLastCandidateId: (candidateId: string | null) => void
  setLastOfferId: (offerId: string | null) => void
  setLastTaskId: (taskId: string | null) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      demoContext: defaultDemoContext,
      lastCandidateId: null,
      lastOfferId: null,
      lastTaskId: null,
      setDemoContext: (patch) =>
        set((state) => ({
          demoContext: {
            ...state.demoContext,
            ...patch,
          },
        })),
      resetDemoContext: () =>
        set({
          demoContext: defaultDemoContext,
        }),
      setLastCandidateId: (candidateId) => set({ lastCandidateId: candidateId }),
      setLastOfferId: (offerId) => set({ lastOfferId: offerId }),
      setLastTaskId: (taskId) => set({ lastTaskId: taskId }),
    }),
    {
      name: 'offer-console-store',
    },
  ),
)
