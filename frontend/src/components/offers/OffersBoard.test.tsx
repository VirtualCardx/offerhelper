import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest'

import { OffersBoard } from '@/components/offers/OffersBoard'
import type {
  CandidateResponse,
  CompanyResponse,
  CompensationStrategyResponse,
  DepartmentResponse,
  OfferRecommendationResponse,
  PositionResponse,
} from '@/types/api'

let mockLastCandidateId: string | null = null

vi.mock('@/store/useAppStore', () => ({
  useAppStore: () => ({
    lastCandidateId: mockLastCandidateId,
  }),
}))

const candidates: CandidateResponse[] = [
  {
    id: 'candidate-1',
    companyId: 'company-1',
    departmentId: 'department-1',
    positionId: 'position-1',
    name: 'Alice Zhang',
    currentSalary: '30000',
    expectedSalary: '38000',
    yearsExperience: 5,
    level: 'P6',
    skills: ['growth', 'sql'],
    interviewScore: 90,
    hasOtherOffer: true,
    city: 'Shanghai',
  },
  {
    id: 'candidate-2',
    companyId: 'company-2',
    departmentId: 'department-2',
    positionId: 'position-2',
    name: 'Bob Li',
    currentSalary: '26000',
    expectedSalary: '32000',
    yearsExperience: 4,
    level: 'P5',
    skills: ['salesforce'],
    interviewScore: 84,
    hasOtherOffer: false,
    city: 'Beijing',
  },
]

const strategies: CompensationStrategyResponse[] = [
  {
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
    ],
  },
  {
    id: 'strategy-2',
    companyId: 'company-2',
    name: '销售岗位进取策略',
    budgetPolicy: {
      limit: '36000',
      yellowThreshold: '0.85',
      redThreshold: '0.95',
    },
    factors: [
      {
        factorCode: 'domainCR',
        weight: '0.4',
        min: '0.9',
        target: '1.0',
        max: '1.15',
      },
    ],
  },
]

const companies: CompanyResponse[] = [
  {
    id: 'company-1',
    name: 'NovaTech',
    industry: 'Internet',
    tenantCode: 'nova',
  },
  {
    id: 'company-2',
    name: 'Acme Corp',
    industry: 'Enterprise SaaS',
    tenantCode: 'acme',
  },
]

const departments: DepartmentResponse[] = [
  {
    id: 'department-1',
    companyId: 'company-1',
    name: 'Growth',
    domain: 'Acquisition',
  },
  {
    id: 'department-2',
    companyId: 'company-2',
    name: 'Sales',
    domain: 'B2B',
  },
]

const positions: PositionResponse[] = [
  {
    id: 'position-1',
    companyId: 'company-1',
    title: 'Growth Manager',
    jobFamily: 'Growth',
    levelBand: 'P6',
  },
  {
    id: 'position-2',
    companyId: 'company-2',
    title: 'Sales Manager',
    jobFamily: 'Sales',
    levelBand: 'P5',
  },
]

const offers: OfferRecommendationResponse[] = [
  {
    offerId: 'offer-1',
    candidateId: 'candidate-1',
    marketSnapshotId: 'market-1',
    strategyId: 'strategy-1',
    outcomeStatus: 'PENDING',
    outcomeNotes: null,
    decidedAt: '2026-06-21T09:30:00+08:00',
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
    riskLevel: 'GREEN',
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
  },
  {
    offerId: 'offer-2',
    candidateId: 'candidate-2',
    marketSnapshotId: 'market-2',
    strategyId: 'strategy-2',
    outcomeStatus: 'PENDING',
    outcomeNotes: null,
    decidedAt: '2026-06-22T10:00:00+08:00',
    recommendedOffer: '31000',
    range: {
      min: '29500',
      max: '33000',
    },
    crValue: '1.02',
    acceptProbability: '0.76',
    acceptanceModelVersion: 'acceptance-xgb-0.4.0',
    competitivenessScore: 74,
    confidence: '0.82',
    riskLevel: 'YELLOW',
    riskReasons: ['接近预算黄色阈值'],
    budget: {
      usageRatio: '0.86',
      riskLevel: 'YELLOW',
      exceeded: false,
    },
    equity: {
      equityScore: 78,
      riskLevel: 'MEDIUM',
      message: '略高于同级销售团队中位数',
      P25: '28000',
      P50: '30000',
      P75: '32500',
      inversionDetected: false,
    },
    reportMarkdown: null,
  },
]

function jsonResponse(data: unknown) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
    },
  })
}

function renderOffersBoard(path = '/offers') {
  window.history.replaceState({}, '', path)

  return render(
    <BrowserRouter>
      <Routes>
        <Route path="/offers" element={<OffersBoard />} />
      </Routes>
    </BrowserRouter>,
  )
}

function closeFilterTag(label: string) {
  const tag = getFilterTagsByLabel(label)[0] ?? null
  const closeButton = tag?.querySelector('.ant-tag-close-icon')

  expect(tag).not.toBeNull()
  expect(closeButton).not.toBeNull()

  fireEvent.click(closeButton as Element)
}

function getFilterTagsByLabel(label: string) {
  return screen
    .queryAllByText(label)
    .map((element) => element.closest('.ant-tag'))
    .filter((element): element is HTMLElement => Boolean(element))
}

beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: (listener: (event: { matches: boolean; media: string }) => void) => {
        listener({ matches: false, media: query })
      },
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  })
  Object.defineProperty(window, 'getComputedStyle', {
    writable: true,
    value: vi.fn().mockImplementation(() => ({
      getPropertyValue: () => '',
      scrollbarColor: '',
      overflow: 'auto',
      overflowX: 'auto',
      overflowY: 'auto',
    })),
  })
})

afterEach(() => {
  window.history.replaceState({}, '', '/offers')
  mockLastCandidateId = null
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})

describe('OffersBoard', () => {
  it('renders readable candidate, organization and strategy information for offers', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)

      if (url.includes('/api/v1/candidates')) {
        return Promise.resolve(jsonResponse(candidates))
      }

      if (url.includes('/api/v1/compensation-strategies')) {
        return Promise.resolve(jsonResponse(strategies))
      }

      if (url.includes('/api/v1/org/companies')) {
        return Promise.resolve(jsonResponse(companies))
      }

      if (url.includes('/api/v1/org/departments')) {
        return Promise.resolve(jsonResponse(departments))
      }

      if (url.includes('/api/v1/org/positions')) {
        return Promise.resolve(jsonResponse(positions))
      }

      if (url.endsWith('/api/v1/offers')) {
        return Promise.resolve(jsonResponse(offers))
      }

      if (url.endsWith('/api/v1/offers/offer-1')) {
        return Promise.resolve(jsonResponse(offers[0]))
      }

      throw new Error(`Unexpected request: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    renderOffersBoard()

    expect(await screen.findByText('Alice Zhang')).toBeInTheDocument()
    expect(screen.getByText('Bob Li')).toBeInTheDocument()
    expect(screen.getByText('增长岗位稳态策略')).toBeInTheDocument()
    expect(screen.getByText('P6 / Shanghai')).toBeInTheDocument()
    expect(screen.getByText('NovaTech / Growth')).toBeInTheDocument()
    expect(screen.getByText('Growth Manager / P6')).toBeInTheDocument()
    expect(screen.getByText('共 2 条 Offer')).toBeInTheDocument()
    expect(screen.getByText('当前排序：最新决策优先')).toBeInTheDocument()
    expect(screen.queryByText('当前筛选')).not.toBeInTheDocument()
    expect(document.body.textContent?.indexOf('Bob Li')).toBeLessThan(document.body.textContent?.indexOf('Alice Zhang') ?? Infinity)

    fireEvent.click(screen.getAllByRole('button', { name: '查看详情' })[1])

    expect(await screen.findByText(/候选人：Alice Zhang/)).toBeInTheDocument()
    expect(screen.getByText(/公司：NovaTech \/ Internet/)).toBeInTheDocument()
    expect(screen.getByText(/部门：Growth \/ Acquisition/)).toBeInTheDocument()
    expect(screen.getByText(/岗位：Growth Manager \/ P6/)).toBeInTheDocument()
    expect(screen.getByText(/策略名称：增长岗位稳态策略/)).toBeInTheDocument()
    expect(document.body.textContent).toContain('候选人 ID：candidat...')
    expect(document.body.textContent).toContain('策略 ID：strategy...')
    expect(document.body.textContent).toContain('市场快照 ID：market-1')

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalled()
    })
  })

  it('clears active filters and restores full offer results', async () => {
    mockLastCandidateId = 'candidate-1'

    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)

      if (url.includes('/api/v1/candidates')) {
        return Promise.resolve(jsonResponse(candidates))
      }

      if (url.includes('/api/v1/compensation-strategies')) {
        return Promise.resolve(jsonResponse(strategies))
      }

      if (url.includes('/api/v1/org/companies')) {
        return Promise.resolve(jsonResponse(companies))
      }

      if (url.includes('/api/v1/org/departments')) {
        return Promise.resolve(jsonResponse(departments))
      }

      if (url.includes('/api/v1/org/positions')) {
        return Promise.resolve(jsonResponse(positions))
      }

      if (url.includes('/api/v1/offers?candidateId=candidate-1')) {
        return Promise.resolve(jsonResponse([offers[0]]))
      }

      if (url.endsWith('/api/v1/offers')) {
        return Promise.resolve(jsonResponse(offers))
      }

      throw new Error(`Unexpected request: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    renderOffersBoard()

    expect(await screen.findByText('共 1 条 Offer')).toBeInTheDocument()
    expect(screen.getAllByText('Alice Zhang').length).toBeGreaterThan(0)
    expect(screen.getByText('当前筛选')).toBeInTheDocument()
    expect(screen.getByText('候选人：Alice Zhang / P6')).toBeInTheDocument()
    expect(window.location.search).toContain('candidateId=candidate-1')

    const clearButton = screen
      .getAllByRole('button', { name: '清空筛选' })
      .find((button) => !button.hasAttribute('disabled'))

    expect(clearButton).toBeDefined()
    fireEvent.click(clearButton as HTMLButtonElement)

    expect((await screen.findAllByText('共 2 条 Offer')).length).toBeGreaterThan(0)
    expect(screen.getAllByText('Bob Li').length).toBeGreaterThan(0)
    expect(screen.queryByText('当前筛选')).not.toBeInTheDocument()
    expect(window.location.search).toBe('')

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/offers?candidateId=candidate-1'), expect.any(Object))
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/offers'), expect.any(Object))
    })
  })

  it('hydrates filters from URL search params and shows filter tags', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)

      if (url.includes('/api/v1/candidates')) {
        return Promise.resolve(jsonResponse(candidates))
      }

      if (url.includes('/api/v1/compensation-strategies')) {
        return Promise.resolve(jsonResponse(strategies))
      }

      if (url.includes('/api/v1/org/companies')) {
        return Promise.resolve(jsonResponse(companies))
      }

      if (url.includes('/api/v1/org/departments')) {
        return Promise.resolve(jsonResponse(departments))
      }

      if (url.includes('/api/v1/org/positions')) {
        return Promise.resolve(jsonResponse(positions))
      }

      if (url.includes('/api/v1/offers?candidateId=candidate-1&riskLevel=GREEN')) {
        return Promise.resolve(jsonResponse([offers[0]]))
      }

      if (url.endsWith('/api/v1/offers')) {
        return Promise.resolve(jsonResponse(offers))
      }

      throw new Error(`Unexpected request: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    renderOffersBoard('/offers?candidateId=candidate-1&riskLevel=GREEN&sortBy=recommendedOfferAsc')

    expect(await screen.findByText('共 1 条 Offer')).toBeInTheDocument()
    expect(screen.getByText('当前排序：推荐薪资从低到高')).toBeInTheDocument()
    expect(screen.getByText('当前筛选')).toBeInTheDocument()
    expect(screen.getByText('候选人：Alice Zhang / P6')).toBeInTheDocument()
    expect(screen.getByText('风险：GREEN')).toBeInTheDocument()
    expect(getFilterTagsByLabel('排序：推荐薪资从低到高').length).toBeGreaterThan(0)
    expect(window.location.search).toContain('candidateId=candidate-1')
    expect(window.location.search).toContain('riskLevel=GREEN')
    expect(window.location.search).toContain('sortBy=recommendedOfferAsc')

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/offers?candidateId=candidate-1&riskLevel=GREEN'), expect.any(Object))
    })
  })

  it('removes a sort tag and restores default sorting state', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)

      if (url.includes('/api/v1/candidates')) {
        return Promise.resolve(jsonResponse(candidates))
      }

      if (url.includes('/api/v1/compensation-strategies')) {
        return Promise.resolve(jsonResponse(strategies))
      }

      if (url.includes('/api/v1/org/companies')) {
        return Promise.resolve(jsonResponse(companies))
      }

      if (url.includes('/api/v1/org/departments')) {
        return Promise.resolve(jsonResponse(departments))
      }

      if (url.includes('/api/v1/org/positions')) {
        return Promise.resolve(jsonResponse(positions))
      }

      if (url.endsWith('/api/v1/offers')) {
        return Promise.resolve(jsonResponse(offers))
      }

      throw new Error(`Unexpected request: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    renderOffersBoard('/offers?sortBy=recommendedOfferAsc')

    expect((await screen.findAllByText('当前筛选')).length).toBeGreaterThan(0)
    expect(getFilterTagsByLabel('排序：推荐薪资从低到高').length).toBeGreaterThan(0)
    expect(screen.getAllByText('当前排序：推荐薪资从低到高').length).toBeGreaterThan(0)
    expect(window.location.search).toContain('sortBy=recommendedOfferAsc')

    closeFilterTag('排序：推荐薪资从低到高')

    await waitFor(() => {
      expect(screen.getAllByText('当前排序：最新决策优先').length).toBeGreaterThan(0)
      expect(window.location.search).not.toContain('sortBy=')
    })
  })

  it('removes a company filter tag and clears dependent org filters in URL', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)

      if (url.includes('/api/v1/candidates')) {
        return Promise.resolve(jsonResponse(candidates))
      }

      if (url.includes('/api/v1/compensation-strategies')) {
        return Promise.resolve(jsonResponse(strategies))
      }

      if (url.includes('/api/v1/org/companies')) {
        return Promise.resolve(jsonResponse(companies))
      }

      if (url.includes('/api/v1/org/departments')) {
        return Promise.resolve(jsonResponse(departments))
      }

      if (url.includes('/api/v1/org/positions')) {
        return Promise.resolve(jsonResponse(positions))
      }

      if (url.endsWith('/api/v1/offers')) {
        return Promise.resolve(jsonResponse(offers))
      }

      throw new Error(`Unexpected request: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    renderOffersBoard('/offers?companyId=company-1&departmentId=department-1&positionId=position-1&strategyId=strategy-1')

    expect((await screen.findAllByText('当前筛选')).length).toBeGreaterThan(0)
    expect(getFilterTagsByLabel('公司：NovaTech').length).toBeGreaterThan(0)
    expect(getFilterTagsByLabel('部门：Growth').length).toBeGreaterThan(0)
    expect(getFilterTagsByLabel('岗位：Growth Manager / P6').length).toBeGreaterThan(0)
    expect(getFilterTagsByLabel('策略：增长岗位稳态策略').length).toBeGreaterThan(0)

    closeFilterTag('公司：NovaTech')

    await waitFor(() => {
      expect(getFilterTagsByLabel('公司：NovaTech')).toHaveLength(0)
      expect(getFilterTagsByLabel('部门：Growth')).toHaveLength(0)
      expect(getFilterTagsByLabel('岗位：Growth Manager / P6')).toHaveLength(0)
      expect(getFilterTagsByLabel('策略：增长岗位稳态策略')).toHaveLength(0)
      expect(window.location.search).toBe('')
    })
  })

  it('removes a candidate filter tag and refreshes full offer results', async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)

      if (url.includes('/api/v1/candidates')) {
        return Promise.resolve(jsonResponse(candidates))
      }

      if (url.includes('/api/v1/compensation-strategies')) {
        return Promise.resolve(jsonResponse(strategies))
      }

      if (url.includes('/api/v1/org/companies')) {
        return Promise.resolve(jsonResponse(companies))
      }

      if (url.includes('/api/v1/org/departments')) {
        return Promise.resolve(jsonResponse(departments))
      }

      if (url.includes('/api/v1/org/positions')) {
        return Promise.resolve(jsonResponse(positions))
      }

      if (url.includes('/api/v1/offers?candidateId=candidate-1')) {
        return Promise.resolve(jsonResponse([offers[0]]))
      }

      if (url.endsWith('/api/v1/offers')) {
        return Promise.resolve(jsonResponse(offers))
      }

      throw new Error(`Unexpected request: ${url}`)
    })

    vi.stubGlobal('fetch', fetchMock)

    renderOffersBoard('/offers?candidateId=candidate-1')

    expect(await screen.findByText('共 1 条 Offer')).toBeInTheDocument()
    expect(getFilterTagsByLabel('候选人：Alice Zhang / P6').length).toBeGreaterThan(0)

    closeFilterTag('候选人：Alice Zhang / P6')

    expect((await screen.findAllByText('共 2 条 Offer')).length).toBeGreaterThan(0)

    await waitFor(() => {
      expect(window.location.search).not.toContain('candidateId=')
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/offers?candidateId=candidate-1'), expect.any(Object))
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/api/v1/offers'), expect.any(Object))
    })
  })

})
