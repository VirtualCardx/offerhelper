import type {
  CandidateResponse,
  CompanyResponse,
  CompensationStrategyResponse,
  DepartmentResponse,
  EmployeeSalaryResponse,
  GovernanceAlertResponse,
  GovernanceEventResponse,
  GovernanceNotificationResponse,
  MarketSalaryResponse,
  ModelVersionResponse,
  OfferRecommendationResponse,
  PositionResponse,
  TaskDispatchResponse,
  TaskScheduleResponse,
  TaskStatusResponse,
  TrainingRunResponse,
} from '@/types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

type QueryValue = string | number | boolean | null | undefined

async function requestJson<T>(
  path: string,
  init?: RequestInit,
  query?: Record<string, QueryValue>,
): Promise<T> {
  const origin =
    typeof window !== 'undefined' && window.location?.origin ? window.location.origin : 'http://127.0.0.1:5173'
  const url = new URL(`${API_BASE_URL}${path}`, origin)
  Object.entries(query ?? {}).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      url.searchParams.set(key, String(value))
    }
  })

  const response = await fetch(url.toString(), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
  })

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Request failed: ${response.status}`)
  }

  return (await response.json()) as T
}

async function requestVoid(path: string, init?: RequestInit): Promise<void> {
  const origin =
    typeof window !== 'undefined' && window.location?.origin ? window.location.origin : 'http://127.0.0.1:5173'
  const response = await fetch(new URL(`${API_BASE_URL}${path}`, origin).toString(), init)
  if (!response.ok) {
    throw new Error((await response.text()) || `Request failed: ${response.status}`)
  }
}

export const api = {
  listCompanies() {
    return requestJson<CompanyResponse[]>('/org/companies')
  },
  listDepartments(companyId?: string) {
    return requestJson<DepartmentResponse[]>('/org/departments', undefined, { companyId })
  },
  listPositions(companyId?: string) {
    return requestJson<PositionResponse[]>('/org/positions', undefined, { companyId })
  },
  listStrategies(companyId?: string) {
    return requestJson<CompensationStrategyResponse[]>('/compensation-strategies', undefined, { companyId })
  },
  createCandidate(payload: Record<string, unknown>) {
    return requestJson<CandidateResponse>('/candidates', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  listCandidates(query?: Record<string, QueryValue>) {
    return requestJson<CandidateResponse[]>('/candidates', undefined, query)
  },
  getMarketSalary(positionId: string, city: string) {
    return requestJson<MarketSalaryResponse>('/market-salary', undefined, { positionId, city })
  },
  listMarketSalaryHistory(positionId: string, city: string, limit = 10) {
    return requestJson<MarketSalaryResponse[]>('/market-salary/history', undefined, { positionId, city, limit })
  },
  createMarketSalary(payload: Record<string, unknown>) {
    return requestJson<MarketSalaryResponse>('/market-salary', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  updateMarketSalary(snapshotId: string, payload: Record<string, unknown>) {
    return requestJson<MarketSalaryResponse>(`/market-salary/${snapshotId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
  promoteMarketSalary(snapshotId: string) {
    return requestJson<MarketSalaryResponse>(`/market-salary/${snapshotId}/promote`, {
      method: 'POST',
    })
  },
  deleteMarketSalary(snapshotId: string) {
    return requestVoid(`/market-salary/${snapshotId}`, {
      method: 'DELETE',
    })
  },
  createEmployeeSalary(payload: Record<string, unknown>) {
    return requestJson<EmployeeSalaryResponse>('/employee-salary', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  updateEmployeeSalary(recordId: string, payload: Record<string, unknown>) {
    return requestJson<EmployeeSalaryResponse>(`/employee-salary/${recordId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
  deleteEmployeeSalary(recordId: string) {
    return requestVoid(`/employee-salary/${recordId}`, {
      method: 'DELETE',
    })
  },
  listEmployeeSalary(companyId: string, departmentId: string, level: string) {
    return requestJson<EmployeeSalaryResponse[]>('/employee-salary', undefined, {
      companyId,
      departmentId,
      level,
    })
  },
  createCompensationStrategy(payload: Record<string, unknown>) {
    return requestJson<CompensationStrategyResponse>('/compensation-strategies', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  updateCompensationStrategy(strategyId: string, payload: Record<string, unknown>) {
    return requestJson<CompensationStrategyResponse>(`/compensation-strategies/${strategyId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
  deleteCompensationStrategy(strategyId: string) {
    return requestVoid(`/compensation-strategies/${strategyId}`, {
      method: 'DELETE',
    })
  },
  recommendAndSaveOffer(payload: Record<string, unknown>) {
    return requestJson<OfferRecommendationResponse>('/offers/recommend-and-save', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  listOffers(query?: Record<string, QueryValue>) {
    return requestJson<OfferRecommendationResponse[]>('/offers', undefined, query)
  },
  getOfferDetail(offerId: string) {
    return requestJson<OfferRecommendationResponse>(`/offers/${offerId}`)
  },
  updateOfferOutcome(offerId: string, payload: Record<string, unknown>) {
    return requestJson<OfferRecommendationResponse>(`/offers/${offerId}/outcome`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  generateOfferReport(offerId: string) {
    return requestJson<{ reportId: string; offerId: string; format: string; content: string }>(
      `/reports/offers/${offerId}/generate`,
      { method: 'POST' },
    )
  },
  getActiveModel(modelName: string) {
    return requestJson<ModelVersionResponse>('/models/active', undefined, { modelName })
  },
  listTrainingRuns(modelName: string) {
    return requestJson<TrainingRunResponse[]>('/models/training-runs', undefined, { modelName })
  },
  listGovernanceEvents(query?: Record<string, QueryValue>) {
    return requestJson<GovernanceEventResponse[]>('/models/governance-events', undefined, query)
  },
  listGovernanceAlerts(query?: Record<string, QueryValue>) {
    return requestJson<GovernanceAlertResponse[]>('/models/governance-alerts', undefined, query)
  },
  reviewGovernanceEvent(eventId: string, payload: Record<string, unknown>) {
    return requestJson(`/models/governance-events/${eventId}/review`, {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  notifyGovernanceAlerts(payload: Record<string, unknown>) {
    return requestJson<GovernanceNotificationResponse>('/models/governance-alerts/notify', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  getTaskSchedules() {
    return requestJson<TaskScheduleResponse[]>('/tasks/schedules')
  },
  getTaskStatus(taskId: string) {
    return requestJson<TaskStatusResponse>(`/tasks/${taskId}`)
  },
  dispatchAlertScan(payload: Record<string, unknown>) {
    return requestJson<TaskDispatchResponse>('/tasks/models/governance-alert-scan', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  dispatchNotifyTask(payload: Record<string, unknown>) {
    return requestJson<TaskDispatchResponse>('/tasks/models/governance-alerts/notify', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}
