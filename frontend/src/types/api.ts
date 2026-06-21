export type CandidateResponse = {
  id: string
  companyId: string
  departmentId: string
  positionId: string
  name: string
  currentSalary: string
  expectedSalary: string | null
  yearsExperience: number
  level: string
  skills: string[]
  interviewScore: number
  hasOtherOffer: boolean
  city: string
}

export type CompanyResponse = {
  id: string
  name: string
  industry: string
  tenantCode: string
}

export type DepartmentResponse = {
  id: string
  companyId: string
  name: string
  domain: string
}

export type PositionResponse = {
  id: string
  companyId: string
  title: string
  jobFamily: string
  levelBand: string
}

export type CompensationStrategyResponse = {
  id: string
  companyId: string
  name: string
  budgetPolicy: {
    limit: string
    yellowThreshold: string
    redThreshold: string
  }
  factors: Array<{
    factorCode: string
    weight: string
    min: string
    target: string
    max: string
  }>
}

export type MarketSalaryResponse = {
  id: string
  positionId: string
  city: string
  P25: string
  P50: string
  P75: string
  source: string
  updateTime: string
}

export type EmployeeSalaryResponse = {
  id: string
  companyId: string
  departmentId: string
  positionId: string
  level: string
  salary: string
}

export type OfferRecommendationResponse = {
  offerId: string
  candidateId: string
  marketSnapshotId?: string | null
  strategyId: string
  outcomeStatus: string
  outcomeNotes: string | null
  decidedAt: string | null
  recommendedOffer: string
  range: {
    min: string
    max: string
  }
  crValue: string
  acceptProbability: string
  acceptanceModelVersion: string
  competitivenessScore: number
  confidence: string
  riskLevel: string
  riskReasons: string[]
  budget: {
    usageRatio: string
    riskLevel: string
    exceeded: boolean
  }
  equity: {
    equityScore: number
    riskLevel: string
    message: string
    P25: string
    P50: string
    P75: string
    inversionDetected: boolean
  }
  reportMarkdown?: string | null
}

export type ModelVersionResponse = {
  id: string
  modelName: string
  modelVersion: string
  framework: string
  status: string
  artifactUri: string
  config: Record<string, unknown>
  metrics: Record<string, unknown>
}

export type TrainingRunResponse = {
  id: string
  modelName: string
  modelVersion: string
  framework: string
  source: string
  status: string
  activationMode: string
  activated: boolean
  activationReason: string
  previousActiveVersion: string | null
  artifactUri: string
  manifestPath: string
  modelPath: string
  sampleCount: number
  acceptanceRate: string
  trainingAccuracy: number
  trainingLogLoss: number
  metrics: Record<string, unknown>
}

export type GovernanceEventResponse = {
  id: string
  modelName: string
  eventType: string
  operator: string
  approvalTicket: string | null
  riskLevel: string
  status: string
  reason: string
  fromVersion: string | null
  toVersion: string | null
  reviewedBy: string | null
  reviewedAt: string | null
  metadata: Record<string, unknown>
  createdAt: string
}

export type GovernanceAlertResponse = {
  id: string
  eventId: string
  modelName: string
  eventType: string
  operator: string
  status: string
  alertType: string
  severity: string
  message: string
  fromVersion: string | null
  toVersion: string | null
  expiresAt: string | null
  createdAt: string
  metadata: Record<string, unknown>
}

export type GovernanceNotificationResponse = {
  channel: string
  destination: string
  deliveryCount: number
  notifiedAlertIds: string[]
  deliveries: Array<{
    id: string
    alertId: string
    channel: string
    destination: string
    subject: string
    body: string
    payload: Record<string, unknown>
  }>
}

export type TaskScheduleResponse = {
  task: string
  cron: string
  description: string
}

export type TaskDispatchResponse = {
  taskId: string
  status: string
}

export type TaskStatusResponse = {
  taskId: string
  status: string
  result: Record<string, unknown> | null
}

export type DemoContext = {
  companyId: string
  departmentId: string
  positionId: string
  strategyId: string
  city: string
  operator: string
  reviewer: string
}

export type WorkspaceRecommendationTraceability = {
  company: CompanyResponse | null
  department: DepartmentResponse | null
  position: PositionResponse | null
  strategy: CompensationStrategyResponse | null
  market: MarketSalaryResponse | null
  selectedPoint: 'min' | 'target' | 'max'
}
