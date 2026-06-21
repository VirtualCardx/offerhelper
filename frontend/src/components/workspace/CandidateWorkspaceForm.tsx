import { Alert, Button, Card, Form, Input, InputNumber, message, Select, Space, Spin, Switch } from 'antd'
import { useEffect, useMemo, useState } from 'react'

import { api } from '@/lib/api'
import { resolveCompanyScopeSelection, resolveScopedId } from '@/lib/context-sync'
import { defaultDemoContext } from '@/lib/demo-defaults'
import { formatCurrency } from '@/lib/format'
import { useAppStore } from '@/store/useAppStore'
import type {
  CandidateResponse,
  CompanyResponse,
  CompensationStrategyResponse,
  DepartmentResponse,
  MarketSalaryResponse,
  OfferRecommendationResponse,
  PositionResponse,
  WorkspaceRecommendationTraceability,
} from '@/types/api'

type CandidateWorkspaceFormProps = {
  onCompleted: (payload: {
    candidate: CandidateResponse
    market: MarketSalaryResponse
    offer: OfferRecommendationResponse
    traceability: WorkspaceRecommendationTraceability
  }) => void
}

type WorkspaceValues = {
  companyId: string
  departmentId: string
  positionId: string
  strategyId: string
  city: string
  name: string
  currentSalary: number
  expectedSalary?: number
  yearsExperience: number
  level: string
  skills: string
  interviewScore: number
  hasOtherOffer: boolean
  selectedPoint: 'min' | 'target' | 'max'
}

type LoadedScope = {
  departmentList: DepartmentResponse[]
  positionList: PositionResponse[]
  strategyList: CompensationStrategyResponse[]
  departmentId: string
  positionId: string
  strategyId: string
}

const defaultWorkspaceValues = {
  name: 'Alice Chen',
  currentSalary: 30000,
  expectedSalary: 38000,
  yearsExperience: 5,
  level: 'P6',
  skills: 'Growth, Strategy, SQL',
  interviewScore: 90,
  hasOtherOffer: true,
  selectedPoint: 'target' as const,
}

export function CandidateWorkspaceForm({ onCompleted }: CandidateWorkspaceFormProps) {
  const [form] = Form.useForm<WorkspaceValues>()
  const { demoContext, setDemoContext, resetDemoContext, setLastCandidateId, setLastOfferId } = useAppStore()
  const [messageApi, contextHolder] = message.useMessage()
  const [loading, setLoading] = useState(false)
  const [bootstrapping, setBootstrapping] = useState(true)
  const [companies, setCompanies] = useState<CompanyResponse[]>([])
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [positions, setPositions] = useState<PositionResponse[]>([])
  const [strategies, setStrategies] = useState<CompensationStrategyResponse[]>([])
  const [previewMarket, setPreviewMarket] = useState<MarketSalaryResponse | null>(null)
  const [previewMarketLoading, setPreviewMarketLoading] = useState(false)
  const watchedCompanyId = Form.useWatch('companyId', form)
  const watchedDepartmentId = Form.useWatch('departmentId', form)
  const watchedPositionId = Form.useWatch('positionId', form)
  const watchedStrategyId = Form.useWatch('strategyId', form)
  const watchedCity = Form.useWatch('city', form)

  const selectedCompany = useMemo(
    () => companies.find((item) => item.id === watchedCompanyId) ?? null,
    [companies, watchedCompanyId],
  )
  const selectedDepartment = useMemo(
    () => departments.find((item) => item.id === watchedDepartmentId) ?? null,
    [departments, watchedDepartmentId],
  )
  const selectedPosition = useMemo(
    () => positions.find((item) => item.id === watchedPositionId) ?? null,
    [positions, watchedPositionId],
  )
  const selectedStrategy = useMemo(
    () => strategies.find((item) => item.id === watchedStrategyId) ?? null,
    [strategies, watchedStrategyId],
  )

  useEffect(() => {
    async function bootstrap() {
      try {
        const companyList = await api.listCompanies()
        const fallbackCompanyId = demoContext.companyId || companyList[0]?.id || ''
        setCompanies(companyList)
        if (fallbackCompanyId) {
          const scope = await loadCompanyScope(fallbackCompanyId, {
            departmentId: demoContext.departmentId,
            positionId: demoContext.positionId,
            strategyId: demoContext.strategyId,
          })
          form.setFieldsValue({
            companyId: fallbackCompanyId,
            departmentId: scope.departmentId,
            positionId: scope.positionId,
            strategyId: scope.strategyId,
            city: demoContext.city || 'Shanghai',
          })
        }
      } catch (error) {
        messageApi.error(error instanceof Error ? error.message : '加载基础组织数据失败。')
      } finally {
        setBootstrapping(false)
      }
    }

    void bootstrap()
  }, [])

  useEffect(() => {
    if (bootstrapping) {
      return
    }

    async function syncFromContext() {
      const values = form.getFieldsValue()
      const nextCompanyId = demoContext.companyId || values.companyId || companies[0]?.id || ''
      if (!nextCompanyId) {
        return
      }

      const shouldReloadScope =
        nextCompanyId !== values.companyId || departments.length === 0 || positions.length === 0 || strategies.length === 0

      if (shouldReloadScope) {
        try {
          const scope = await loadCompanyScope(nextCompanyId, {
            departmentId: demoContext.departmentId || values.departmentId,
            positionId: demoContext.positionId || values.positionId,
            strategyId: demoContext.strategyId || values.strategyId,
          })
          form.setFieldsValue({
            companyId: nextCompanyId,
            departmentId: scope.departmentId,
            positionId: scope.positionId,
            strategyId: scope.strategyId,
            city: demoContext.city || values.city || 'Shanghai',
          })
        } catch (error) {
          messageApi.error(error instanceof Error ? error.message : '同步数据维护中心上下文失败。')
        }
        return
      }

      form.setFieldsValue({
        companyId: nextCompanyId,
        departmentId: resolveScopedId(departments, demoContext.departmentId || values.departmentId),
        positionId: resolveScopedId(positions, demoContext.positionId || values.positionId),
        strategyId: resolveScopedId(strategies, demoContext.strategyId || values.strategyId),
        city: demoContext.city || values.city || 'Shanghai',
      })
    }

    void syncFromContext()
  }, [bootstrapping, companies, demoContext, departments, form, messageApi, positions, strategies])

  useEffect(() => {
    if (!watchedPositionId || !watchedCity) {
      setPreviewMarket(null)
      return
    }

    async function loadPreviewMarket() {
      try {
        setPreviewMarketLoading(true)
        const market = await api.getMarketSalary(watchedPositionId, watchedCity)
        setPreviewMarket(market)
      } catch {
        setPreviewMarket(null)
      } finally {
        setPreviewMarketLoading(false)
      }
    }

    void loadPreviewMarket()
  }, [watchedCity, watchedPositionId])

  async function loadCompanyScope(
    companyId: string,
    preferred: {
      departmentId?: string
      positionId?: string
      strategyId?: string
    } = {},
  ): Promise<LoadedScope> {
    const [departmentList, positionList, strategyList] = await Promise.all([
      api.listDepartments(companyId),
      api.listPositions(companyId),
      api.listStrategies(companyId),
    ])

    setDepartments(departmentList)
    setPositions(positionList)
    setStrategies(strategyList)

    const scope = resolveCompanyScopeSelection({
      departments: departmentList,
      positions: positionList,
      strategies: strategyList,
      preferredDepartmentId: preferred.departmentId,
      preferredPositionId: preferred.positionId,
      preferredStrategyId: preferred.strategyId,
    })

    return {
      departmentList,
      positionList,
      strategyList,
      ...scope,
    }
  }

  async function handleCompanyChange(companyId: string) {
    form.setFieldsValue({
      companyId,
      departmentId: undefined,
      positionId: undefined,
      strategyId: undefined,
    })

    try {
      const scope = await loadCompanyScope(companyId)
      form.setFieldsValue({
        departmentId: scope.departmentId,
        positionId: scope.positionId,
        strategyId: scope.strategyId,
      })
      setDemoContext({
        companyId,
        departmentId: scope.departmentId,
        positionId: scope.positionId,
        strategyId: scope.strategyId,
      })
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '切换公司后加载资源失败。')
    }
  }

  async function handleResetContext() {
    const fallbackCompanyId = companies[0]?.id ?? ''
    resetDemoContext()

    if (!fallbackCompanyId) {
      form.setFieldsValue({
        ...defaultWorkspaceValues,
        city: defaultDemoContext.city,
      })
      messageApi.success('已恢复默认上下文。')
      return
    }

    try {
      const scope = await loadCompanyScope(fallbackCompanyId)
      form.setFieldsValue({
        ...defaultWorkspaceValues,
        companyId: fallbackCompanyId,
        departmentId: scope.departmentId,
        positionId: scope.positionId,
        strategyId: scope.strategyId,
        city: defaultDemoContext.city,
      })
      messageApi.success('已恢复默认上下文。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '恢复默认上下文失败。')
    }
  }

  function handleResetForm() {
    form.setFieldsValue({
      ...defaultWorkspaceValues,
      companyId: watchedCompanyId,
      departmentId: watchedDepartmentId,
      positionId: watchedPositionId,
      strategyId: watchedStrategyId,
      city: watchedCity || demoContext.city || defaultDemoContext.city,
    })
  }

  async function handleFinish(values: WorkspaceValues) {
    try {
      setLoading(true)
      const candidate = await api.createCandidate({
        companyId: values.companyId,
        departmentId: values.departmentId,
        positionId: values.positionId,
        name: values.name,
        currentSalary: values.currentSalary,
        expectedSalary: values.expectedSalary ?? null,
        yearsExperience: values.yearsExperience,
        level: values.level,
        skills: values.skills.split(',').map((item) => item.trim()).filter(Boolean),
        interviewScore: values.interviewScore,
        hasOtherOffer: values.hasOtherOffer,
        city: values.city,
      })

      const market = await api.getMarketSalary(values.positionId, values.city)
      const offer = await api.recommendAndSaveOffer({
        candidateId: candidate.id,
        strategyId: values.strategyId,
        selectedPoint: values.selectedPoint,
        city: values.city,
      })
      const traceability = {
        company: companies.find((item) => item.id === values.companyId) ?? null,
        department: departments.find((item) => item.id === values.departmentId) ?? null,
        position: positions.find((item) => item.id === values.positionId) ?? null,
        strategy: strategies.find((item) => item.id === values.strategyId) ?? null,
        market,
        selectedPoint: values.selectedPoint,
      } satisfies WorkspaceRecommendationTraceability

      setDemoContext({
        companyId: values.companyId,
        departmentId: values.departmentId,
        positionId: values.positionId,
        strategyId: values.strategyId,
        city: values.city,
      })
      setLastCandidateId(candidate.id)
      setLastOfferId(offer.offerId)
      onCompleted({ candidate, market, offer, traceability })
      messageApi.success('候选人已创建并生成 Offer 推荐。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '生成 Offer 失败。')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="glass-card" styles={{ body: { padding: 24 } }}>
      {contextHolder}
      <div className="mb-6">
        <div className="text-xs tracking-[0.22em] text-zinc-500 uppercase">候选人工作台</div>
        <div className="mt-2 font-serif text-2xl text-white">一键生成候选人推荐薪酬</div>
      </div>
      <Alert
        className="mb-6"
        type="info"
        showIcon
        message="与数据维护中心联动"
        description="公司、部门、岗位、策略和城市会与数据维护中心共享上下文。切到“数据维护中心”创建新策略或维护市场数据后，返回此处会自动带入最新范围。"
      />

      <Spin spinning={bootstrapping}>
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            city: demoContext.city,
            ...defaultWorkspaceValues,
          }}
          onFinish={handleFinish}
        >
          <div className="mb-6 grid gap-4 xl:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="text-xs tracking-[0.18em] text-zinc-500 uppercase">当前范围</div>
              <div className="mt-3 text-sm text-zinc-200">
                <div>{selectedCompany ? `${selectedCompany.name} / ${selectedCompany.industry}` : '等待选择公司'}</div>
                <div className="mt-2">{selectedDepartment ? `${selectedDepartment.name} / ${selectedDepartment.domain}` : '等待选择部门'}</div>
                <div className="mt-2">{selectedPosition ? `${selectedPosition.title} / ${selectedPosition.levelBand}` : '等待选择岗位'}</div>
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="text-xs tracking-[0.18em] text-zinc-500 uppercase">策略预览</div>
              <div className="mt-3 text-sm text-zinc-200">
                {selectedStrategy ? (
                  <>
                    <div>{selectedStrategy.name}</div>
                    <div className="mt-2">策略 ID {`${selectedStrategy.id.slice(0, 8)}...`}</div>
                    <div className="mt-2">预算上限 {formatCurrency(selectedStrategy.budgetPolicy.limit)}</div>
                    <div className="mt-2">
                      阈值 {selectedStrategy.budgetPolicy.yellowThreshold} / {selectedStrategy.budgetPolicy.redThreshold}
                    </div>
                    <div className="mt-2">CR 因子 {selectedStrategy.factors.length} 个</div>
                  </>
                ) : (
                  <div>等待选择策略</div>
                )}
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
              <div className="text-xs tracking-[0.18em] text-zinc-500 uppercase">市场快照预览</div>
              <Spin spinning={previewMarketLoading}>
                <div className="mt-3 text-sm text-zinc-200">
                  {previewMarket ? (
                    <>
                      <div>{previewMarket.city}</div>
                      <div className="mt-2">快照 ID {`${previewMarket.id.slice(0, 8)}...`}</div>
                      <div className="mt-2">P50 {formatCurrency(previewMarket.P50)}</div>
                      <div className="mt-2">P75 {formatCurrency(previewMarket.P75)}</div>
                      <div className="mt-2">来源 {previewMarket.source}</div>
                    </>
                  ) : (
                    <div>当前岗位与城市暂无市场快照。</div>
                  )}
                </div>
              </Spin>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Form.Item label="公司" name="companyId" rules={[{ required: true }]}>
              <Select
                placeholder="选择公司"
                onChange={(value) => void handleCompanyChange(value)}
                options={companies.map((item) => ({
                  value: item.id,
                  label: `${item.name} / ${item.industry}`,
                }))}
              />
            </Form.Item>
            <Form.Item label="部门" name="departmentId" rules={[{ required: true }]}>
              <Select
                placeholder="选择部门"
                onChange={(value) => setDemoContext({ departmentId: value })}
                options={departments.map((item) => ({
                  value: item.id,
                  label: `${item.name} / ${item.domain}`,
                }))}
              />
            </Form.Item>
            <Form.Item label="岗位" name="positionId" rules={[{ required: true }]}>
              <Select
                placeholder="选择岗位"
                onChange={(value) => setDemoContext({ positionId: value })}
                options={positions.map((item) => ({
                  value: item.id,
                  label: `${item.title} / ${item.levelBand}`,
                }))}
              />
            </Form.Item>
            <Form.Item label="策略" name="strategyId" rules={[{ required: true }]}>
              <Select
                placeholder="选择策略"
                onChange={(value) => setDemoContext({ strategyId: value })}
                options={strategies.map((item) => ({
                  value: item.id,
                  label: item.name,
                }))}
              />
            </Form.Item>
          <Form.Item label="候选人姓名" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="城市" name="city" rules={[{ required: true }]}>
            <Input onChange={(event) => setDemoContext({ city: event.target.value })} />
          </Form.Item>
          <Form.Item label="当前薪资" name="currentSalary" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={1000} step={1000} />
          </Form.Item>
          <Form.Item label="期望薪资" name="expectedSalary">
            <InputNumber className="w-full" min={1000} step={1000} />
          </Form.Item>
          <Form.Item label="工作年限" name="yearsExperience" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={0} max={30} />
          </Form.Item>
          <Form.Item label="级别" name="level" rules={[{ required: true }]}>
            <Select options={[{ value: 'P5' }, { value: 'P6' }, { value: 'P7' }]} />
          </Form.Item>
          <Form.Item label="技能标签" name="skills" rules={[{ required: true }]}>
            <Input placeholder="以逗号分隔" />
          </Form.Item>
          <Form.Item label="面试评分" name="interviewScore" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={0} max={100} />
          </Form.Item>
          <Form.Item label="推荐锚点" name="selectedPoint" rules={[{ required: true }]}>
            <Select
              options={[
                { label: '保守 min', value: 'min' },
                { label: '平衡 target', value: 'target' },
                { label: '激进 max', value: 'max' },
              ]}
            />
          </Form.Item>
          <Form.Item label="已有其他 Offer" name="hasOtherOffer" valuePropName="checked">
            <Switch />
          </Form.Item>
          </div>

          <Space className="mt-4" size="middle">
            <Button size="large" type="primary" htmlType="submit" loading={loading}>
              创建候选人并生成 Offer
            </Button>
            <Button size="large" onClick={handleResetForm}>
              重置表单
            </Button>
            <Button size="large" onClick={() => void handleResetContext()}>
              恢复默认上下文
            </Button>
          </Space>
        </Form>
      </Spin>
    </Card>
  )
}
