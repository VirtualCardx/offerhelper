import { Button, Card, Drawer, Select, Space, Table, Tag, message } from 'antd'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { api } from '@/lib/api'
import { formatCurrency, formatDateTime, formatPercent } from '@/lib/format'
import { useAppStore } from '@/store/useAppStore'
import type {
  CandidateResponse,
  CompanyResponse,
  CompensationStrategyResponse,
  DepartmentResponse,
  OfferRecommendationResponse,
  PositionResponse,
} from '@/types/api'

type OfferSortKey =
  | 'decidedAtDesc'
  | 'decidedAtAsc'
  | 'recommendedOfferDesc'
  | 'recommendedOfferAsc'
  | 'acceptProbabilityDesc'
  | 'riskLevelDesc'

type OfferFilterState = {
  candidateId: string
  companyId: string
  departmentId: string
  positionId: string
  strategyId: string
  riskLevel: string | undefined
  sortBy: OfferSortKey
}

type ActiveFilterTag = {
  key: keyof OfferFilterState
  label: string
}

const defaultOfferSortKey: OfferSortKey = 'decidedAtDesc'
const validRiskLevels = ['GREEN', 'YELLOW', 'RED'] as const
const offerSortOptions: Array<{ value: OfferSortKey; label: string }> = [
  { value: 'decidedAtDesc', label: '最新决策优先' },
  { value: 'decidedAtAsc', label: '最早决策优先' },
  { value: 'recommendedOfferDesc', label: '推荐薪资从高到低' },
  { value: 'recommendedOfferAsc', label: '推荐薪资从低到高' },
  { value: 'acceptProbabilityDesc', label: '接受概率从高到低' },
  { value: 'riskLevelDesc', label: '风险等级从高到低' },
]

function riskPriority(riskLevel: OfferRecommendationResponse['riskLevel']) {
  if (riskLevel === 'RED') return 3
  if (riskLevel === 'YELLOW') return 2
  return 1
}

function isOfferSortKey(value: string | null): value is OfferSortKey {
  return offerSortOptions.some((item) => item.value === value)
}

function createInitialFilterState(searchParams: URLSearchParams, fallbackCandidateId: string): OfferFilterState {
  const riskLevel = searchParams.get('riskLevel')
  const sortBy = searchParams.get('sortBy')

  return {
    candidateId: searchParams.get('candidateId') ?? fallbackCandidateId,
    companyId: searchParams.get('companyId') ?? '',
    departmentId: searchParams.get('departmentId') ?? '',
    positionId: searchParams.get('positionId') ?? '',
    strategyId: searchParams.get('strategyId') ?? '',
    riskLevel: validRiskLevels.includes((riskLevel ?? '') as (typeof validRiskLevels)[number]) ? riskLevel ?? undefined : undefined,
    sortBy: isOfferSortKey(sortBy) ? sortBy : defaultOfferSortKey,
  }
}

export function OffersBoard() {
  const { lastCandidateId } = useAppStore()
  const [searchParams, setSearchParams] = useSearchParams()
  const initialFilterStateRef = useRef<OfferFilterState | null>(null)

  if (initialFilterStateRef.current === null) {
    initialFilterStateRef.current = createInitialFilterState(searchParams, lastCandidateId ?? '')
  }

  const initialFilterState = initialFilterStateRef.current
  const [candidateId, setCandidateId] = useState(initialFilterState.candidateId)
  const [companyId, setCompanyId] = useState<string>(initialFilterState.companyId)
  const [departmentId, setDepartmentId] = useState<string>(initialFilterState.departmentId)
  const [positionId, setPositionId] = useState<string>(initialFilterState.positionId)
  const [strategyId, setStrategyId] = useState<string>(initialFilterState.strategyId)
  const [riskLevel, setRiskLevel] = useState<string | undefined>(initialFilterState.riskLevel)
  const [sortBy, setSortBy] = useState<OfferSortKey>(initialFilterState.sortBy)
  const [offers, setOffers] = useState<OfferRecommendationResponse[]>([])
  const [candidates, setCandidates] = useState<CandidateResponse[]>([])
  const [strategies, setStrategies] = useState<CompensationStrategyResponse[]>([])
  const [companies, setCompanies] = useState<CompanyResponse[]>([])
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [positions, setPositions] = useState<PositionResponse[]>([])
  const [selectedOffer, setSelectedOffer] = useState<OfferRecommendationResponse | null>(null)
  const [messageApi, contextHolder] = message.useMessage()

  async function refresh(nextCandidateId = candidateId, nextRisk = riskLevel) {
    try {
      const data = await api.listOffers({
        candidateId: nextCandidateId || undefined,
        riskLevel: nextRisk,
      })
      setOffers(data)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '加载 Offer 列表失败。')
    }
  }

  async function openOffer(offerId: string) {
    try {
      const detail = await api.getOfferDetail(offerId)
      setSelectedOffer(detail)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '加载 Offer 详情失败。')
    }
  }

  async function updateOutcome(outcomeStatus: 'ACCEPTED' | 'REJECTED') {
    if (!selectedOffer) return
    const detail = await api.updateOfferOutcome(selectedOffer.offerId, {
      outcomeStatus,
      outcomeNotes: outcomeStatus === 'ACCEPTED' ? '前端工作台标记已接受。' : '前端工作台标记已拒绝。',
    })
    setSelectedOffer(detail)
    await refresh()
  }

  async function generateReport() {
    if (!selectedOffer) return
    await api.generateOfferReport(selectedOffer.offerId)
    await openOffer(selectedOffer.offerId)
    messageApi.success('报告已生成并回写到 Offer 详情。')
  }

  useEffect(() => {
    async function bootstrap() {
      const [candidateResult, strategyResult, companyResult, departmentResult, positionResult] = await Promise.allSettled([
        api.listCandidates({ limit: 50 }),
        api.listStrategies(),
        api.listCompanies(),
        api.listDepartments(),
        api.listPositions(),
      ])

      if (candidateResult.status === 'fulfilled') {
        setCandidates(candidateResult.value)
      }

      if (strategyResult.status === 'fulfilled') {
        setStrategies(strategyResult.value)
      }

      if (companyResult.status === 'fulfilled') {
        setCompanies(companyResult.value)
      }

      if (departmentResult.status === 'fulfilled') {
        setDepartments(departmentResult.value)
      }

      if (positionResult.status === 'fulfilled') {
        setPositions(positionResult.value)
      }

      await refresh(initialFilterState.candidateId, initialFilterState.riskLevel)
    }

    void bootstrap()
  }, [initialFilterState])

  const candidateById = useMemo(
    () => new Map(candidates.map((candidate) => [candidate.id, candidate])),
    [candidates],
  )
  const strategyById = useMemo(
    () => new Map(strategies.map((strategy) => [strategy.id, strategy])),
    [strategies],
  )
  const companyById = useMemo(
    () => new Map(companies.map((company) => [company.id, company])),
    [companies],
  )
  const departmentById = useMemo(
    () => new Map(departments.map((department) => [department.id, department])),
    [departments],
  )
  const positionById = useMemo(
    () => new Map(positions.map((position) => [position.id, position])),
    [positions],
  )

  useEffect(() => {
    const nextSearchParams = new URLSearchParams()

    if (candidateId) {
      nextSearchParams.set('candidateId', candidateId)
    }

    if (companyId) {
      nextSearchParams.set('companyId', companyId)
    }

    if (departmentId) {
      nextSearchParams.set('departmentId', departmentId)
    }

    if (positionId) {
      nextSearchParams.set('positionId', positionId)
    }

    if (strategyId) {
      nextSearchParams.set('strategyId', strategyId)
    }

    if (riskLevel) {
      nextSearchParams.set('riskLevel', riskLevel)
    }

    if (sortBy !== defaultOfferSortKey) {
      nextSearchParams.set('sortBy', sortBy)
    }

    const nextSearch = nextSearchParams.toString()

    if (nextSearch !== searchParams.toString()) {
      setSearchParams(nextSearchParams, { replace: true })
    }
  }, [candidateId, companyId, departmentId, positionId, riskLevel, searchParams, setSearchParams, sortBy, strategyId])

  function getOfferContext(offer: OfferRecommendationResponse) {
    const candidate = candidateById.get(offer.candidateId)
    const strategy = strategyById.get(offer.strategyId)
    const company = companyById.get(candidate?.companyId ?? strategy?.companyId ?? '')
    const department = departmentById.get(candidate?.departmentId ?? '')
    const position = positionById.get(candidate?.positionId ?? '')

    return {
      candidate,
      strategy,
      company,
      department,
      position,
    }
  }

  const columns = useMemo(
    () => [
      {
        title: '候选人',
        dataIndex: 'candidateId',
        key: 'candidate',
        render: (value: string, record: OfferRecommendationResponse) => {
          const { candidate } = getOfferContext(record)
          return (
            <div>
              <div>{candidate?.name ?? '--'}</div>
              <div className="text-xs text-zinc-400">{candidate ? `${candidate.level} / ${candidate.city}` : value.slice(0, 8) + '...'}</div>
            </div>
          )
        },
      },
      {
        title: '组织范围',
        key: 'orgScope',
        render: (_: unknown, record: OfferRecommendationResponse) => {
          const { company, department, position } = getOfferContext(record)
          return (
            <div>
              <div>{[company?.name, department?.name].filter(Boolean).join(' / ') || '--'}</div>
              <div className="text-xs text-zinc-400">{position ? `${position.title} / ${position.levelBand}` : '--'}</div>
            </div>
          )
        },
      },
      {
        title: 'Offer ID',
        dataIndex: 'offerId',
        key: 'offerId',
        render: (value: string) => <span className="text-xs text-zinc-400">{value.slice(0, 8)}...</span>,
      },
      {
        title: '市场快照',
        dataIndex: 'marketSnapshotId',
        key: 'marketSnapshotId',
        render: (value?: string | null) => <span className="text-xs text-zinc-400">{value ? `${value.slice(0, 8)}...` : '--'}</span>,
      },
      {
        title: '策略',
        dataIndex: 'strategyId',
        key: 'strategyId',
        render: (value: string) => {
          const strategy = strategyById.get(value)
          return (
            <div>
              <div>{strategy?.name ?? '--'}</div>
              <div className="text-xs text-zinc-400">{`${value.slice(0, 8)}...`}</div>
            </div>
          )
        },
      },
      {
        title: '推荐薪资',
        dataIndex: 'recommendedOffer',
        key: 'recommendedOffer',
        render: (value: string) => formatCurrency(value),
      },
      {
        title: '接受概率',
        dataIndex: 'acceptProbability',
        key: 'acceptProbability',
        render: (value: string) => formatPercent(value),
      },
      {
        title: '风险',
        dataIndex: 'riskLevel',
        key: 'riskLevel',
        render: (value: string) => <Tag color={value === 'RED' ? 'red' : value === 'YELLOW' ? 'gold' : 'cyan'}>{value}</Tag>,
      },
      {
        title: '结果状态',
        dataIndex: 'outcomeStatus',
        key: 'outcomeStatus',
      },
      {
        title: '操作',
        key: 'action',
        render: (_: unknown, record: OfferRecommendationResponse) => (
          <Button type="link" onClick={() => void openOffer(record.offerId)}>
            查看详情
          </Button>
        ),
      },
    ],
    [candidateById, companyById, departmentById, positionById, strategyById],
  )
  const selectedOfferContext = selectedOffer ? getOfferContext(selectedOffer) : null
  const filteredOffers = useMemo(
    () =>
      offers.filter((offer) => {
        const { candidate, strategy, company, department, position } = getOfferContext(offer)

        if (companyId && company?.id !== companyId) {
          return false
        }

        if (departmentId && department?.id !== departmentId) {
          return false
        }

        if (positionId && position?.id !== positionId) {
          return false
        }

        if (strategyId && strategy?.id !== strategyId) {
          return false
        }

        return candidateId ? candidate?.id === candidateId : true
      }),
    [candidateId, companyId, departmentId, offers, positionId, strategyId],
  )
  const departmentOptions = useMemo(
    () => departments.filter((department) => !companyId || department.companyId === companyId),
    [companyId, departments],
  )
  const positionOptions = useMemo(
    () => positions.filter((position) => !companyId || position.companyId === companyId),
    [companyId, positions],
  )
  const strategyOptions = useMemo(
    () => strategies.filter((strategy) => !companyId || strategy.companyId === companyId),
    [companyId, strategies],
  )

  function handleCompanyChange(value?: string) {
    const nextCompanyId = value ?? ''
    setCompanyId(nextCompanyId)

    if (nextCompanyId) {
      if (departmentId) {
        const department = departmentById.get(departmentId)
        if (department && department.companyId !== nextCompanyId) {
          setDepartmentId('')
        }
      }

      if (positionId) {
        const position = positionById.get(positionId)
        if (position && position.companyId !== nextCompanyId) {
          setPositionId('')
        }
      }

      if (strategyId) {
        const strategy = strategyById.get(strategyId)
        if (strategy && strategy.companyId !== nextCompanyId) {
          setStrategyId('')
        }
      }
    }
  }

  useEffect(() => {
    if (!companyId) {
      return
    }

    if (departmentId) {
      const department = departmentById.get(departmentId)

      if (department && department.companyId !== companyId) {
        setDepartmentId('')
      }
    }

    if (positionId) {
      const position = positionById.get(positionId)

      if (position && position.companyId !== companyId) {
        setPositionId('')
      }
    }

    if (strategyId) {
      const strategy = strategyById.get(strategyId)

      if (strategy && strategy.companyId !== companyId) {
        setStrategyId('')
      }
    }
  }, [companyId, departmentId, departmentById, positionId, positionById, strategyById, strategyId])

  function resetFilters() {
    setCandidateId('')
    setCompanyId('')
    setDepartmentId('')
    setPositionId('')
    setStrategyId('')
    setRiskLevel(undefined)
    setSortBy(defaultOfferSortKey)
    void refresh('', undefined)
  }

  function removeFilterTag(key: ActiveFilterTag['key']) {
    if (key === 'candidateId') {
      setCandidateId('')
      void refresh('', riskLevel)
      return
    }

    if (key === 'companyId') {
      setCompanyId('')
      setDepartmentId('')
      setPositionId('')
      setStrategyId('')
      return
    }

    if (key === 'departmentId') {
      setDepartmentId('')
      return
    }

    if (key === 'positionId') {
      setPositionId('')
      return
    }

    if (key === 'strategyId') {
      setStrategyId('')
      return
    }

    if (key === 'riskLevel') {
      setRiskLevel(undefined)
      void refresh(candidateId, undefined)
      return
    }

    setSortBy(defaultOfferSortKey)
  }

  const displayedOffers = useMemo(() => {
    const nextOffers = [...filteredOffers]

    nextOffers.sort((left, right) => {
      if (sortBy === 'decidedAtAsc') {
        return new Date(left.decidedAt).getTime() - new Date(right.decidedAt).getTime()
      }

      if (sortBy === 'recommendedOfferDesc') {
        return Number(right.recommendedOffer) - Number(left.recommendedOffer)
      }

      if (sortBy === 'recommendedOfferAsc') {
        return Number(left.recommendedOffer) - Number(right.recommendedOffer)
      }

      if (sortBy === 'acceptProbabilityDesc') {
        return Number(right.acceptProbability) - Number(left.acceptProbability)
      }

      if (sortBy === 'riskLevelDesc') {
        return riskPriority(right.riskLevel) - riskPriority(left.riskLevel)
      }

      return new Date(right.decidedAt).getTime() - new Date(left.decidedAt).getTime()
    })

    return nextOffers
  }, [filteredOffers, sortBy])
  const hasActiveFilters = Boolean(
    candidateId || companyId || departmentId || positionId || strategyId || riskLevel || sortBy !== 'decidedAtDesc',
  )
  const resultSummary =
    displayedOffers.length === offers.length
      ? `共 ${displayedOffers.length} 条 Offer`
      : `当前命中 ${displayedOffers.length} 条 / 已加载 ${offers.length} 条`
  const activeFilterTags = useMemo(() => {
    const tags: ActiveFilterTag[] = []
    const candidate = candidateId ? candidateById.get(candidateId) : undefined
    const company = companyId ? companyById.get(companyId) : undefined
    const department = departmentId ? departmentById.get(departmentId) : undefined
    const position = positionId ? positionById.get(positionId) : undefined
    const strategy = strategyId ? strategyById.get(strategyId) : undefined
    const sortLabel = offerSortOptions.find((item) => item.value === sortBy)?.label ?? '最新决策优先'

    if (candidateId) {
      tags.push({
        key: 'candidateId',
        label: `候选人：${candidate ? `${candidate.name} / ${candidate.level}` : candidateId.slice(0, 8)}`,
      })
    }

    if (companyId) {
      tags.push({
        key: 'companyId',
        label: `公司：${company ? company.name : companyId.slice(0, 8)}`,
      })
    }

    if (departmentId) {
      tags.push({
        key: 'departmentId',
        label: `部门：${department ? department.name : departmentId.slice(0, 8)}`,
      })
    }

    if (positionId) {
      tags.push({
        key: 'positionId',
        label: `岗位：${position ? `${position.title} / ${position.levelBand}` : positionId.slice(0, 8)}`,
      })
    }

    if (strategyId) {
      tags.push({
        key: 'strategyId',
        label: `策略：${strategy ? strategy.name : strategyId.slice(0, 8)}`,
      })
    }

    if (riskLevel) {
      tags.push({
        key: 'riskLevel',
        label: `风险：${riskLevel}`,
      })
    }

    if (sortBy !== defaultOfferSortKey) {
      tags.push({
        key: 'sortBy',
        label: `排序：${sortLabel}`,
      })
    }

    return tags
  }, [candidateById, candidateId, companyById, companyId, departmentById, departmentId, positionById, positionId, riskLevel, sortBy, strategyById, strategyId])

  return (
    <>
      {contextHolder}
      <Card className="glass-card" styles={{ body: { padding: 24 } }}>
        <div className="mb-5 flex flex-wrap items-end gap-3">
          <Select
            allowClear
            showSearch
            className="min-w-72"
            placeholder="按候选人过滤"
            value={candidateId}
            onChange={(value) => setCandidateId(value ?? '')}
            options={candidates.map((item) => ({
              value: item.id,
              label: `${item.name} / ${item.level} / ${item.city}`,
            }))}
          />
          <Select
            allowClear
            showSearch
            className="min-w-56"
            placeholder="公司"
            value={companyId || undefined}
            onChange={(value) => handleCompanyChange(value)}
            options={companies.map((item) => ({
              value: item.id,
              label: `${item.name} / ${item.industry}`,
            }))}
          />
          <Select
            allowClear
            showSearch
            className="min-w-52"
            placeholder="部门"
            value={departmentId || undefined}
            onChange={(value) => setDepartmentId(value ?? '')}
            options={departmentOptions.map((item) => ({
              value: item.id,
              label: `${item.name} / ${item.domain}`,
            }))}
          />
          <Select
            allowClear
            showSearch
            className="min-w-56"
            placeholder="岗位"
            value={positionId || undefined}
            onChange={(value) => setPositionId(value ?? '')}
            options={positionOptions.map((item) => ({
              value: item.id,
              label: `${item.title} / ${item.levelBand}`,
            }))}
          />
          <Select
            allowClear
            showSearch
            className="min-w-56"
            placeholder="策略"
            value={strategyId || undefined}
            onChange={(value) => setStrategyId(value ?? '')}
            options={strategyOptions.map((item) => ({
              value: item.id,
              label: item.name,
            }))}
          />
          <Select
            allowClear
            className="min-w-40"
            placeholder="风险等级"
            value={riskLevel}
            onChange={(value) => setRiskLevel(value)}
            options={[{ value: 'GREEN' }, { value: 'YELLOW' }, { value: 'RED' }]}
          />
          <Select
            className="min-w-48"
            value={sortBy}
            onChange={(value) => setSortBy(value)}
            options={offerSortOptions}
          />
          <Button type="primary" onClick={() => void refresh()}>
            查询 Offer
          </Button>
          <Button onClick={resetFilters} disabled={!hasActiveFilters}>
            清空筛选
          </Button>
        </div>

        <div className="mb-3 flex flex-wrap items-center justify-between gap-3 text-sm text-zinc-500">
          <div>{resultSummary}</div>
          <div>当前排序：{offerSortOptions.find((item) => item.value === sortBy)?.label ?? '最新决策优先'}</div>
        </div>

        {activeFilterTags.length > 0 ? (
          <div className="mb-4 flex flex-wrap items-center gap-2 text-sm text-zinc-500">
            <span>当前筛选</span>
            {activeFilterTags.map((tag) => (
              <Tag key={tag.key} closable onClose={() => removeFilterTag(tag.key)}>
                {tag.label}
              </Tag>
            ))}
          </div>
        ) : null}

        <Table
          rowKey="offerId"
          columns={columns}
          dataSource={displayedOffers}
          pagination={{ pageSize: 6 }}
          className="offer-table"
        />
      </Card>

      <Drawer
        title="Offer 详情"
        placement="right"
        width={560}
        open={Boolean(selectedOffer)}
        onClose={() => setSelectedOffer(null)}
      >
        {selectedOffer ? (
          <div className="space-y-4">
            {selectedOfferContext ? (
              <>
                <div className="rounded-2xl border border-zinc-200 p-4">
                  <div>候选人：{selectedOfferContext.candidate?.name ?? '--'}</div>
                  <div>候选人 ID：{`${selectedOffer.candidateId.slice(0, 8)}...`}</div>
                  <div>
                    公司：
                    {selectedOfferContext.company
                      ? `${selectedOfferContext.company.name} / ${selectedOfferContext.company.industry}`
                      : '--'}
                  </div>
                  <div>
                    部门：
                    {selectedOfferContext.department
                      ? `${selectedOfferContext.department.name} / ${selectedOfferContext.department.domain}`
                      : '--'}
                  </div>
                  <div>
                    岗位：
                    {selectedOfferContext.position
                      ? `${selectedOfferContext.position.title} / ${selectedOfferContext.position.levelBand}`
                      : '--'}
                  </div>
                  <div>策略名称：{selectedOfferContext.strategy?.name ?? '--'}</div>
                  <div>策略 ID：{`${selectedOffer.strategyId.slice(0, 8)}...`}</div>
                  <div>市场快照 ID：{selectedOffer.marketSnapshotId ? `${selectedOffer.marketSnapshotId.slice(0, 8)}...` : '--'}</div>
                </div>
                <div className="rounded-2xl border border-zinc-200 p-4">
                  <div>推荐薪资：{formatCurrency(selectedOffer.recommendedOffer)}</div>
                  <div>接受概率：{formatPercent(selectedOffer.acceptProbability)}</div>
                  <div>风险等级：{selectedOffer.riskLevel}</div>
                  <div>结果状态：{selectedOffer.outcomeStatus}</div>
                  <div>决策时间：{formatDateTime(selectedOffer.decidedAt)}</div>
                </div>
                <div className="rounded-2xl border border-zinc-200 p-4">
                  <div className="font-medium">风险原因</div>
                  <ul className="mt-2 list-disc pl-5">
                    {selectedOffer.riskReasons.map((reason) => (
                      <li key={reason}>{reason}</li>
                    ))}
                  </ul>
                </div>
                <Space wrap>
                  <Button onClick={() => void updateOutcome('ACCEPTED')}>标记已接受</Button>
                  <Button danger onClick={() => void updateOutcome('REJECTED')}>
                    标记已拒绝
                  </Button>
                  <Button type="primary" onClick={() => void generateReport()}>
                    生成报告
                  </Button>
                </Space>
                <div className="rounded-2xl border border-zinc-200 p-4">
                  <div className="font-medium">报告摘要</div>
                  <div className="mt-2 whitespace-pre-wrap text-sm text-zinc-600">
                    {selectedOffer.reportMarkdown ?? '尚未生成报告。'}
                  </div>
                </div>
              </>
            ) : null}
          </div>
        ) : null}
      </Drawer>
    </>
  )
}
