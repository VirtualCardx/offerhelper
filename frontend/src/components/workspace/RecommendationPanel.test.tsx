import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { RecommendationPanel } from '@/components/workspace/RecommendationPanel'
import type { MarketSalaryResponse, OfferRecommendationResponse, WorkspaceRecommendationTraceability } from '@/types/api'

vi.mock('echarts-for-react', () => ({
  default: () => <div data-testid="competitiveness-chart" />,
}))

const market: MarketSalaryResponse = {
  id: 'market-1',
  positionId: 'position-1',
  city: 'Shanghai',
  P25: '25000',
  P50: '35000',
  P75: '45000',
  source: 'Radford 2026 Q2',
  updateTime: '2026-06-20T10:30:00+08:00',
}

const offer: OfferRecommendationResponse = {
  offerId: 'offer-1',
  candidateId: 'candidate-1',
  strategyId: 'strategy-1',
  outcomeStatus: 'PENDING',
  outcomeNotes: null,
  decidedAt: null,
  recommendedOffer: '38000',
  range: {
    min: '36000',
    max: '40000',
  },
  crValue: '1.08',
  acceptProbability: '0.85',
  acceptanceModelVersion: 'acceptance-xgb-0.4.0',
  competitivenessScore: 87,
  confidence: '0.89',
  riskLevel: 'LOW',
  riskReasons: ['市场处于 P50-P75 之间', '预算使用率可控'],
  budget: {
    usageRatio: '0.95',
    riskLevel: 'LOW',
    exceeded: false,
  },
  equity: {
    equityScore: 85,
    riskLevel: 'LOW',
    message: 'Offer 在团队合理范围内',
    P25: '34000',
    P50: '36000',
    P75: '39000',
    inversionDetected: false,
  },
  reportMarkdown: null,
}

const traceability: WorkspaceRecommendationTraceability = {
  company: {
    id: 'company-1',
    name: 'NovaTech',
    industry: 'Internet',
    tenantCode: 'nova',
  },
  department: {
    id: 'department-1',
    companyId: 'company-1',
    name: 'Growth',
    domain: 'Acquisition',
  },
  position: {
    id: 'position-1',
    companyId: 'company-1',
    title: 'Growth Manager',
    jobFamily: 'Growth',
    levelBand: 'P6',
  },
  strategy: {
    id: 'strategy-1',
    companyId: 'company-1',
    name: '增长岗位稳态策略',
    budgetPolicy: {
      limit: '45000',
      yellowThreshold: '0.9',
      redThreshold: '1.0',
    },
    factors: [
      {
        factorCode: 'companyCR',
        weight: '0.3',
        min: '0.8',
        target: '1.0',
        max: '1.1',
      },
      {
        factorCode: 'talentCR',
        weight: '0.2',
        min: '1.0',
        target: '1.15',
        max: '1.3',
      },
    ],
  },
  market,
  selectedPoint: 'target',
}

describe('RecommendationPanel', () => {
  it('renders strategy and market traceability details', () => {
    render(<RecommendationPanel market={market} offer={offer} traceability={traceability} />)

    expect(screen.getByText('本次推荐依据')).toBeInTheDocument()
    expect(screen.getByText('策略快照')).toBeInTheDocument()
    expect(screen.getByText('市场快照')).toBeInTheDocument()
    expect(screen.getByText('增长岗位稳态策略')).toBeInTheDocument()
    expect(screen.getByText(/组织范围 NovaTech \/ Growth/)).toBeInTheDocument()
    expect(screen.getByText(/业务摘要 Internet \/ Acquisition/)).toBeInTheDocument()
    expect(screen.getByText(/策略 ID strategy/)).toBeInTheDocument()
    expect(screen.getByText(/推荐锚点 平衡 target/)).toBeInTheDocument()
    expect(screen.getByText(/快照 ID market-1/)).toBeInTheDocument()
    expect(screen.getByText(/报告来源 Radford 2026 Q2/)).toBeInTheDocument()
    expect(screen.getByText(/岗位 Growth Manager/)).toBeInTheDocument()
    expect(document.body.textContent).toContain('本次推荐基于 NovaTech / Growth 下的 Growth Manager 在 Shanghai 的市场快照')
  })
})
