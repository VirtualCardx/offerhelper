type ScopedOption = {
  id: string
}

type CompanyScopeInput = {
  departments: ScopedOption[]
  positions: ScopedOption[]
  strategies: ScopedOption[]
  preferredDepartmentId?: string | null
  preferredPositionId?: string | null
  preferredStrategyId?: string | null
}

export type CompanyScopeSelection = {
  departmentId: string
  positionId: string
  strategyId: string
}

export function resolveScopedId<T extends ScopedOption>(
  items: T[],
  preferredId?: string | null,
): string {
  if (preferredId && items.some((item) => item.id === preferredId)) {
    return preferredId
  }

  return items[0]?.id ?? ''
}

export function resolveCompanyScopeSelection({
  departments,
  positions,
  strategies,
  preferredDepartmentId,
  preferredPositionId,
  preferredStrategyId,
}: CompanyScopeInput): CompanyScopeSelection {
  return {
    departmentId: resolveScopedId(departments, preferredDepartmentId),
    positionId: resolveScopedId(positions, preferredPositionId),
    strategyId: resolveScopedId(strategies, preferredStrategyId),
  }
}
