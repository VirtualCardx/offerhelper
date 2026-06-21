import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  message,
} from 'antd'
import { useEffect, useMemo, useState } from 'react'

import { api } from '@/lib/api'
import { resolveCompanyScopeSelection } from '@/lib/context-sync'
import { defaultDemoContext } from '@/lib/demo-defaults'
import { formatCurrency, formatDateTime } from '@/lib/format'
import { useAppStore } from '@/store/useAppStore'
import type {
  CompanyResponse,
  CompensationStrategyResponse,
  DepartmentResponse,
  EmployeeSalaryResponse,
  MarketSalaryResponse,
  PositionResponse,
} from '@/types/api'

const defaultFactors = [
  { factorCode: 'company', weight: 0.3, min: 0.8, target: 1.0, max: 1.1 },
  { factorCode: 'domain', weight: 0.3, min: 0.9, target: 1.05, max: 1.2 },
  { factorCode: 'department', weight: 0.2, min: 0.95, target: 1.0, max: 1.15 },
  { factorCode: 'talent', weight: 0.2, min: 1.0, target: 1.15, max: 1.3 },
]

type StrategyFormValues = {
  name: string
  limit: number
  yellowThreshold: number
  redThreshold: number
}

type MarketFormValues = {
  city: string
  source: string
  P25: number
  P50: number
  P75: number
}

type SalaryFormValues = {
  positionId: string
  level: string
  salary: number
}

type CompanyScope = {
  departmentId: string
  positionId: string
  strategyId: string
}

export function DataHubConsole() {
  const { demoContext, setDemoContext, resetDemoContext } = useAppStore()
  const [messageApi, contextHolder] = message.useMessage()
  const [strategyForm] = Form.useForm<StrategyFormValues>()
  const [marketForm] = Form.useForm<MarketFormValues>()
  const [salaryForm] = Form.useForm<SalaryFormValues>()
  const [editMarketForm] = Form.useForm<MarketFormValues>()
  const [editSalaryForm] = Form.useForm<SalaryFormValues>()
  const [editStrategyForm] = Form.useForm<StrategyFormValues>()

  const [bootstrapping, setBootstrapping] = useState(true)
  const [companyId, setCompanyId] = useState(demoContext.companyId)
  const [departmentId, setDepartmentId] = useState(demoContext.departmentId)
  const [positionId, setPositionId] = useState(demoContext.positionId)
  const [city, setCity] = useState(demoContext.city || 'Shanghai')
  const [level, setLevel] = useState('P6')

  const [companies, setCompanies] = useState<CompanyResponse[]>([])
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [positions, setPositions] = useState<PositionResponse[]>([])
  const [strategies, setStrategies] = useState<CompensationStrategyResponse[]>([])
  const [marketSnapshot, setMarketSnapshot] = useState<MarketSalaryResponse | null>(null)
  const [marketSnapshots, setMarketSnapshots] = useState<MarketSalaryResponse[]>([])
  const [salaryRecords, setSalaryRecords] = useState<EmployeeSalaryResponse[]>([])
  const [editingMarketSnapshot, setEditingMarketSnapshot] = useState<MarketSalaryResponse | null>(null)
  const [editingSalaryRecord, setEditingSalaryRecord] = useState<EmployeeSalaryResponse | null>(null)
  const [editingStrategy, setEditingStrategy] = useState<CompensationStrategyResponse | null>(null)
  const [modalSubmitting, setModalSubmitting] = useState(false)

  async function loadCompanyScope(
    nextCompanyId: string,
    preferredDepartmentId = departmentId,
    preferredPositionId = positionId,
    preferredStrategyId = demoContext.strategyId,
  ): Promise<CompanyScope> {
    const [departmentList, positionList, strategyList] = await Promise.all([
      api.listDepartments(nextCompanyId),
      api.listPositions(nextCompanyId),
      api.listStrategies(nextCompanyId),
    ])
    setDepartments(departmentList)
    setPositions(positionList)
    setStrategies(strategyList)

    const {
      departmentId: nextDepartmentId,
      positionId: nextPositionId,
      strategyId: nextStrategyId,
    } = resolveCompanyScopeSelection({
      departments: departmentList,
      positions: positionList,
      strategies: strategyList,
      preferredDepartmentId,
      preferredPositionId,
      preferredStrategyId,
    })
    setDepartmentId(nextDepartmentId)
    setPositionId(nextPositionId)
    setDemoContext({
      companyId: nextCompanyId,
      departmentId: nextDepartmentId,
      positionId: nextPositionId,
      strategyId: nextStrategyId,
    })
    salaryForm.setFieldValue('positionId', nextPositionId)

    return {
      departmentId: nextDepartmentId,
      positionId: nextPositionId,
      strategyId: nextStrategyId,
    }
  }

  async function refreshMarket(nextPositionId = positionId, nextCity = city) {
    if (!nextPositionId || !nextCity) {
      setMarketSnapshot(null)
      setMarketSnapshots([])
      return
    }

    const [latestResult, historyResult] = await Promise.allSettled([
      api.getMarketSalary(nextPositionId, nextCity),
      api.listMarketSalaryHistory(nextPositionId, nextCity, 10),
    ])

    if (latestResult.status === 'fulfilled') {
      setMarketSnapshot(latestResult.value)
    } else {
      setMarketSnapshot(null)
    }

    if (historyResult.status === 'fulfilled') {
      setMarketSnapshots(historyResult.value)
    } else {
      setMarketSnapshots([])
    }
  }

  async function refreshSalaryRecords(nextCompanyId = companyId, nextDepartmentId = departmentId, nextLevel = level) {
    if (!nextCompanyId || !nextDepartmentId || !nextLevel) {
      setSalaryRecords([])
      return
    }
    try {
      const records = await api.listEmployeeSalary(nextCompanyId, nextDepartmentId, nextLevel)
      setSalaryRecords(records)
    } catch {
      setSalaryRecords([])
    }
  }

  async function bootstrap() {
    try {
      const companyList = await api.listCompanies()
      const nextCompanyId = companyId || companyList[0]?.id || ''
      setCompanies(companyList)
      setCompanyId(nextCompanyId)
      const scope = await loadCompanyScope(nextCompanyId)
      await Promise.all([
        refreshMarket(scope.positionId, city),
        refreshSalaryRecords(nextCompanyId, scope.departmentId, level),
      ])
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '加载数据维护中心失败。')
    } finally {
      setBootstrapping(false)
    }
  }

  async function handleCompanyChange(nextCompanyId: string) {
    setCompanyId(nextCompanyId)
    try {
      const scope = await loadCompanyScope(nextCompanyId)
      await Promise.all([
        refreshMarket(scope.positionId, city),
        refreshSalaryRecords(nextCompanyId, scope.departmentId, level),
      ])
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '切换公司上下文失败。')
    }
  }

  async function handleResetContext() {
    resetDemoContext()
    setCity(defaultDemoContext.city)
    setLevel('P6')

    try {
      const companyList = await api.listCompanies()
      const fallbackCompanyId = companyList[0]?.id ?? ''
      setCompanies(companyList)
      setCompanyId(fallbackCompanyId)
      if (!fallbackCompanyId) {
        setDepartments([])
        setPositions([])
        setStrategies([])
        setDepartmentId('')
        setPositionId('')
        setMarketSnapshot(null)
        setMarketSnapshots([])
        setSalaryRecords([])
        messageApi.success('已恢复默认上下文。')
        return
      }

      const scope = await loadCompanyScope(
        fallbackCompanyId,
        defaultDemoContext.departmentId,
        defaultDemoContext.positionId,
        defaultDemoContext.strategyId,
      )
      await Promise.all([
        refreshMarket(scope.positionId, defaultDemoContext.city),
        refreshSalaryRecords(fallbackCompanyId, scope.departmentId, 'P6'),
      ])
      messageApi.success('已恢复默认上下文。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '恢复默认上下文失败。')
    }
  }

  useEffect(() => {
    void bootstrap()
  }, [])

  useEffect(() => {
    strategyForm.setFieldsValue({
      name: 'Default Strategy Copy',
      limit: 40000,
      yellowThreshold: 1.0,
      redThreshold: 1.1,
    })
  }, [])

  useEffect(() => {
    marketForm.setFieldsValue({
      city,
      source: 'manual-console',
      P25: 25000,
      P50: 35000,
      P75: 45000,
    })
  }, [city])

  useEffect(() => {
    salaryForm.setFieldsValue({
      positionId,
      level,
      salary: 36000,
    })
  }, [positionId, level])

  const strategyColumns = useMemo(
    () => [
      { title: '策略名', dataIndex: 'name', key: 'name' },
      {
        title: '预算上限',
        dataIndex: ['budgetPolicy', 'limit'],
        key: 'limit',
        render: (value: string) => formatCurrency(value),
      },
      {
        title: '因子数',
        dataIndex: 'factors',
        key: 'factors',
        render: (value: CompensationStrategyResponse['factors']) => value.length,
      },
      {
        title: '操作',
        key: 'actions',
        render: (_: unknown, record: CompensationStrategyResponse) => (
          <Space>
            <Button type="link" onClick={() => openEditStrategy(record)}>
              编辑
            </Button>
            <Popconfirm
              title="删除策略"
              description="删除后将无法在工作台继续使用该策略。"
              onConfirm={() => void handleDeleteStrategy(record)}
            >
              <Button danger type="link">
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [],
  )

  const salaryColumns = useMemo(
    () => [
      { title: '级别', dataIndex: 'level', key: 'level', render: (value: string) => <Tag color="cyan">{value}</Tag> },
      { title: '薪资', dataIndex: 'salary', key: 'salary', render: (value: string) => formatCurrency(value) },
      { title: '岗位 ID', dataIndex: 'positionId', key: 'positionId', render: (value: string) => `${value.slice(0, 8)}...` },
      {
        title: '操作',
        key: 'actions',
        render: (_: unknown, record: EmployeeSalaryResponse) => (
          <Space>
            <Button type="link" onClick={() => openEditSalary(record)}>
              编辑
            </Button>
            <Popconfirm title="删除员工薪资" onConfirm={() => void handleDeleteSalary(record)}>
              <Button danger type="link">
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [],
  )

  const marketHistoryColumns = useMemo(
    () => [
      {
        title: '版本',
        key: 'version',
        render: (_: unknown, record: MarketSalaryResponse, index: number) =>
          index === 0 || record.id === marketSnapshot?.id ? <Tag color="gold">当前最新</Tag> : <Tag>历史</Tag>,
      },
      {
        title: '快照 ID',
        dataIndex: 'id',
        key: 'id',
        render: (value: string) => `${value.slice(0, 8)}...`,
      },
      { title: 'P50', dataIndex: 'P50', key: 'P50', render: (value: string) => formatCurrency(value) },
      { title: 'P75', dataIndex: 'P75', key: 'P75', render: (value: string) => formatCurrency(value) },
      { title: '来源', dataIndex: 'source', key: 'source' },
      {
        title: '更新时间',
        dataIndex: 'updateTime',
        key: 'updateTime',
        render: (value: string) => formatDateTime(value),
      },
      {
        title: '操作',
        key: 'actions',
        render: (_: unknown, record: MarketSalaryResponse) => (
          <Space>
            {record.id !== marketSnapshot?.id ? (
              <Popconfirm
                title="设为当前市场快照"
                description="这会基于该历史版本创建一个新的最新快照。"
                onConfirm={() => void handlePromoteMarket(record)}
              >
                <Button type="link">设为当前</Button>
              </Popconfirm>
            ) : null}
            <Button type="link" onClick={() => openEditMarket(record)}>
              编辑
            </Button>
            <Popconfirm title="删除市场快照" onConfirm={() => void handleDeleteMarket(record)}>
              <Button danger type="link">
                删除
              </Button>
            </Popconfirm>
          </Space>
        ),
      },
    ],
    [marketSnapshot],
  )

  async function handleCreateMarket(values: Record<string, unknown>) {
    if (!positionId) {
      messageApi.warning('请先选择岗位。')
      return
    }
    await api.createMarketSalary({
      positionId,
      city: values.city,
      P25: values.P25,
      P50: values.P50,
      P75: values.P75,
      source: values.source,
    })
    const nextCity = String(values.city)
    setCity(nextCity)
    setDemoContext({ city: nextCity })
    messageApi.success('市场薪资快照已写入。')
    await refreshMarket(positionId, nextCity)
  }

  function openEditMarket(snapshot: MarketSalaryResponse) {
    setEditingMarketSnapshot(snapshot)
    editMarketForm.setFieldsValue({
      city: snapshot.city,
      source: snapshot.source,
      P25: Number(snapshot.P25),
      P50: Number(snapshot.P50),
      P75: Number(snapshot.P75),
    })
  }

  async function handleCreateSalary(values: Record<string, unknown>) {
    if (!companyId || !departmentId) {
      messageApi.warning('请先选择公司和部门。')
      return
    }
    await api.createEmployeeSalary({
      companyId,
      departmentId,
      positionId: values.positionId,
      level: values.level,
      salary: values.salary,
    })
    messageApi.success('员工薪资记录已新增。')
    await refreshSalaryRecords(companyId, departmentId, String(values.level))
  }

  function openEditSalary(record: EmployeeSalaryResponse) {
    setEditingSalaryRecord(record)
    editSalaryForm.setFieldsValue({
      positionId: record.positionId,
      level: record.level,
      salary: Number(record.salary),
    })
  }

  async function handleCreateStrategy(values: StrategyFormValues) {
    if (!companyId) {
      messageApi.warning('请先选择公司。')
      return
    }
    const strategy = await api.createCompensationStrategy({
      companyId,
      name: values.name,
      budgetPolicy: {
        limit: values.limit,
        yellowThreshold: values.yellowThreshold,
        redThreshold: values.redThreshold,
      },
      factors: defaultFactors,
    })
    messageApi.success('薪酬策略已创建。')
    setDemoContext({ strategyId: strategy.id })
    setStrategies(await api.listStrategies(companyId))
  }

  function openEditStrategy(strategy: CompensationStrategyResponse) {
    setEditingStrategy(strategy)
    editStrategyForm.setFieldsValue({
      name: strategy.name,
      limit: Number(strategy.budgetPolicy.limit),
      yellowThreshold: Number(strategy.budgetPolicy.yellowThreshold),
      redThreshold: Number(strategy.budgetPolicy.redThreshold),
    })
  }

  async function handleUpdateMarket(values: MarketFormValues) {
    if (!editingMarketSnapshot || !positionId) {
      return
    }
    try {
      setModalSubmitting(true)
      const snapshot = await api.updateMarketSalary(editingMarketSnapshot.id, {
        positionId,
        city: values.city,
        P25: values.P25,
        P50: values.P50,
        P75: values.P75,
        source: values.source,
      })
      setEditingMarketSnapshot(null)
      setCity(snapshot.city)
      setDemoContext({ city: snapshot.city })
      await refreshMarket(snapshot.positionId, snapshot.city)
      messageApi.success('市场薪资快照已更新。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '更新市场薪资失败。')
    } finally {
      setModalSubmitting(false)
    }
  }

  async function handleDeleteMarket(snapshot = editingMarketSnapshot) {
    if (!snapshot) {
      return
    }
    try {
      await api.deleteMarketSalary(snapshot.id)
      setEditingMarketSnapshot(null)
      await refreshMarket(snapshot.positionId, snapshot.city)
      messageApi.success('市场薪资快照已删除。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '删除市场薪资失败。')
    }
  }

  async function handlePromoteMarket(snapshot: MarketSalaryResponse) {
    try {
      const promotedSnapshot = await api.promoteMarketSalary(snapshot.id)
      setCity(promotedSnapshot.city)
      setDemoContext({ city: promotedSnapshot.city })
      await refreshMarket(promotedSnapshot.positionId, promotedSnapshot.city)
      messageApi.success('历史市场快照已设为当前版本。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '设为当前市场快照失败。')
    }
  }

  async function handleUpdateSalary(values: SalaryFormValues) {
    if (!editingSalaryRecord || !companyId || !departmentId) {
      return
    }
    try {
      setModalSubmitting(true)
      await api.updateEmployeeSalary(editingSalaryRecord.id, {
        companyId,
        departmentId,
        positionId: values.positionId,
        level: values.level,
        salary: values.salary,
      })
      setEditingSalaryRecord(null)
      await refreshSalaryRecords(companyId, departmentId, values.level)
      messageApi.success('员工薪资记录已更新。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '更新员工薪资失败。')
    } finally {
      setModalSubmitting(false)
    }
  }

  async function handleDeleteSalary(record: EmployeeSalaryResponse) {
    try {
      await api.deleteEmployeeSalary(record.id)
      await refreshSalaryRecords(companyId, departmentId, level)
      messageApi.success('员工薪资记录已删除。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '删除员工薪资失败。')
    }
  }

  async function handleUpdateStrategy(values: StrategyFormValues) {
    if (!editingStrategy) {
      return
    }
    try {
      setModalSubmitting(true)
      const strategy = await api.updateCompensationStrategy(editingStrategy.id, {
        name: values.name,
        budgetPolicy: {
          limit: values.limit,
          yellowThreshold: values.yellowThreshold,
          redThreshold: values.redThreshold,
        },
        factors: editingStrategy.factors,
      })
      setEditingStrategy(null)
      setDemoContext({ strategyId: strategy.id })
      if (companyId) {
        setStrategies(await api.listStrategies(companyId))
      }
      messageApi.success('薪酬策略已更新。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '更新薪酬策略失败。')
    } finally {
      setModalSubmitting(false)
    }
  }

  async function handleDeleteStrategy(strategy: CompensationStrategyResponse) {
    try {
      await api.deleteCompensationStrategy(strategy.id)
      if (companyId) {
        const nextStrategies = await api.listStrategies(companyId)
        setStrategies(nextStrategies)
        const nextStrategyId = nextStrategies[0]?.id ?? ''
        setDemoContext({ strategyId: nextStrategyId })
      }
      messageApi.success('薪酬策略已删除。')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '删除薪酬策略失败。')
    }
  }

  return (
    <>
      {contextHolder}
      <Spin spinning={bootstrapping}>
        <div className="space-y-4">
          <Card className="glass-card" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 flex flex-wrap items-end gap-3">
              <Select
                className="min-w-64"
                placeholder="公司"
                value={companyId || undefined}
                onChange={(value) => {
                  void handleCompanyChange(value)
                }}
                options={companies.map((item) => ({ value: item.id, label: `${item.name} / ${item.industry}` }))}
              />
              <Select
                className="min-w-52"
                placeholder="部门"
                value={departmentId || undefined}
                onChange={(value) => {
                  setDepartmentId(value)
                  setDemoContext({ departmentId: value })
                  void refreshSalaryRecords(companyId, value, level)
                }}
                options={departments.map((item) => ({ value: item.id, label: item.name }))}
              />
              <Select
                className="min-w-56"
                placeholder="岗位"
                value={positionId || undefined}
                onChange={(value) => {
                  setPositionId(value)
                  setDemoContext({ positionId: value })
                  salaryForm.setFieldValue('positionId', value)
                  void refreshMarket(value, city)
                }}
                options={positions.map((item) => ({ value: item.id, label: `${item.title} / ${item.levelBand}` }))}
              />
              <Input
                className="max-w-40"
                value={city}
                onChange={(event) => {
                  const nextCity = event.target.value
                  setCity(nextCity)
                  setDemoContext({ city: nextCity })
                }}
                placeholder="城市"
              />
              <Select
                className="min-w-32"
                value={level}
                onChange={(value) => {
                  setLevel(value)
                  salaryForm.setFieldValue('level', value)
                  void refreshSalaryRecords(companyId, departmentId, value)
                }}
                options={[{ value: 'P5' }, { value: 'P6' }, { value: 'P7' }]}
              />
              <Button onClick={() => void Promise.all([refreshMarket(), refreshSalaryRecords(), companyId ? api.listStrategies(companyId).then(setStrategies) : Promise.resolve([])])}>
                刷新上下文
              </Button>
              <Button onClick={() => void handleResetContext()}>恢复默认上下文</Button>
            </div>
            <Alert
              type="info"
              showIcon
              message="基础数据维护"
              description="在这里维护市场薪资、内部员工薪资和薪酬策略，工作台会直接复用这些真实数据。"
            />
          </Card>

          <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
            <Card className="glass-card" styles={{ body: { padding: 24 } }}>
              <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">市场薪资快照</div>
              <div className="mb-4 rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-zinc-300">
                {marketSnapshot ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Tag color="gold">当前最新</Tag>
                      <span>
                        {city} / {positions.find((item) => item.id === positionId)?.title ?? '当前岗位'}
                      </span>
                    </div>
                    <div>P25：{formatCurrency(marketSnapshot.P25)}</div>
                    <div>P50：{formatCurrency(marketSnapshot.P50)}</div>
                    <div>P75：{formatCurrency(marketSnapshot.P75)}</div>
                    <div>快照 ID：{`${marketSnapshot.id.slice(0, 8)}...`}</div>
                    <div>来源：{marketSnapshot.source}</div>
                    <div>更新时间：{formatDateTime(marketSnapshot.updateTime)}</div>
                    <div className="pt-2">
                      <Space>
                        <Button onClick={() => openEditMarket(marketSnapshot)}>编辑当前快照</Button>
                        <Popconfirm title="删除当前市场快照" onConfirm={() => void handleDeleteMarket(marketSnapshot)}>
                          <Button danger>删除当前快照</Button>
                        </Popconfirm>
                      </Space>
                    </div>
                  </div>
                ) : (
                  <div>当前岗位/城市尚无快照，提交后会立即可用于 Offer 工作台。</div>
                )}
              </div>
              <div className="mb-4">
                <div className="mb-3 text-xs tracking-[0.18em] text-zinc-500 uppercase">历史快照</div>
                <Table
                  rowKey="id"
                  pagination={false}
                  size="small"
                  locale={{ emptyText: '当前范围暂无历史快照。' }}
                  columns={marketHistoryColumns}
                  dataSource={marketSnapshots}
                />
              </div>
              <Form form={marketForm} layout="vertical" onFinish={(values) => void handleCreateMarket(values)}>
                <div className="grid gap-3 md:grid-cols-2">
                  <Form.Item label="城市" name="city" rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item label="来源" name="source" rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item label="P25" name="P25" rules={[{ required: true }]}>
                    <InputNumber className="w-full" min={1000} step={1000} />
                  </Form.Item>
                  <Form.Item label="P50" name="P50" rules={[{ required: true }]}>
                    <InputNumber className="w-full" min={1000} step={1000} />
                  </Form.Item>
                  <Form.Item label="P75" name="P75" rules={[{ required: true }]}>
                    <InputNumber className="w-full" min={1000} step={1000} />
                  </Form.Item>
                </div>
                <Button type="primary" htmlType="submit">
                  保存市场薪资
                </Button>
              </Form>
            </Card>

            <Card className="glass-card" styles={{ body: { padding: 24 } }}>
              <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">员工薪资分布</div>
              <Table rowKey="id" pagination={{ pageSize: 4 }} columns={salaryColumns} dataSource={salaryRecords} />
              <Form form={salaryForm} layout="vertical" onFinish={(values) => void handleCreateSalary(values)}>
                <div className="grid gap-3 md:grid-cols-3">
                  <Form.Item label="岗位" name="positionId" rules={[{ required: true }]}>
                    <Select options={positions.map((item) => ({ value: item.id, label: item.title }))} />
                  </Form.Item>
                  <Form.Item label="级别" name="level" rules={[{ required: true }]}>
                    <Select options={[{ value: 'P5' }, { value: 'P6' }, { value: 'P7' }]} />
                  </Form.Item>
                  <Form.Item label="薪资" name="salary" rules={[{ required: true }]}>
                    <InputNumber className="w-full" min={1000} step={500} />
                  </Form.Item>
                </div>
                <Button type="primary" htmlType="submit">
                  新增员工薪资
                </Button>
              </Form>
            </Card>
          </div>

          <Card className="glass-card" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">薪酬策略维护</div>
            <div className="grid gap-4 xl:grid-cols-[0.92fr_1.08fr]">
              <Form form={strategyForm} layout="vertical" onFinish={(values) => void handleCreateStrategy(values)}>
                <div className="grid gap-3 md:grid-cols-2">
                  <Form.Item label="策略名" name="name" rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                  <Form.Item label="预算上限" name="limit" rules={[{ required: true }]}>
                    <InputNumber className="w-full" min={1000} step={1000} />
                  </Form.Item>
                  <Form.Item label="黄色阈值" name="yellowThreshold" rules={[{ required: true }]}>
                    <InputNumber className="w-full" min={0.5} max={2} step={0.05} />
                  </Form.Item>
                  <Form.Item label="红色阈值" name="redThreshold" rules={[{ required: true }]}>
                    <InputNumber className="w-full" min={0.5} max={2} step={0.05} />
                  </Form.Item>
                </div>
                <div className="mb-4 grid gap-3 md:grid-cols-2">
                  {defaultFactors.map((item) => (
                    <div key={item.factorCode} className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-zinc-300">
                      <div className="mb-2 flex items-center justify-between">
                        <span>{item.factorCode}</span>
                        <Tag color="purple">weight {item.weight}</Tag>
                      </div>
                      <div>
                        {item.min} / {item.target} / {item.max}
                      </div>
                    </div>
                  ))}
                </div>
                <Button type="primary" htmlType="submit">
                  创建策略
                </Button>
              </Form>

              <Table
                rowKey="id"
                pagination={{ pageSize: 5 }}
                columns={strategyColumns}
                dataSource={strategies}
                expandable={{
                  expandedRowRender: (record) => (
                    <div className="space-y-2 text-sm text-zinc-300">
                      {record.factors.map((factor) => (
                        <div key={factor.factorCode}>
                          {factor.factorCode}: {factor.min} / {factor.target} / {factor.max}
                        </div>
                      ))}
                    </div>
                  ),
                }}
              />
            </div>
          </Card>
        </div>
      </Spin>

      <Modal
        title="编辑市场薪资快照"
        open={editingMarketSnapshot !== null}
        onCancel={() => setEditingMarketSnapshot(null)}
        onOk={() => void editMarketForm.submit()}
        confirmLoading={modalSubmitting}
        destroyOnHidden
      >
        <Form form={editMarketForm} layout="vertical" onFinish={(values) => void handleUpdateMarket(values)}>
          <Form.Item label="城市" name="city" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="来源" name="source" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="P25" name="P25" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={1000} step={1000} />
          </Form.Item>
          <Form.Item label="P50" name="P50" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={1000} step={1000} />
          </Form.Item>
          <Form.Item label="P75" name="P75" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={1000} step={1000} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑员工薪资"
        open={editingSalaryRecord !== null}
        onCancel={() => setEditingSalaryRecord(null)}
        onOk={() => void editSalaryForm.submit()}
        confirmLoading={modalSubmitting}
        destroyOnHidden
      >
        <Form form={editSalaryForm} layout="vertical" onFinish={(values) => void handleUpdateSalary(values)}>
          <Form.Item label="岗位" name="positionId" rules={[{ required: true }]}>
            <Select options={positions.map((item) => ({ value: item.id, label: item.title }))} />
          </Form.Item>
          <Form.Item label="级别" name="level" rules={[{ required: true }]}>
            <Select options={[{ value: 'P5' }, { value: 'P6' }, { value: 'P7' }]} />
          </Form.Item>
          <Form.Item label="薪资" name="salary" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={1000} step={500} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑薪酬策略"
        open={editingStrategy !== null}
        onCancel={() => setEditingStrategy(null)}
        onOk={() => void editStrategyForm.submit()}
        confirmLoading={modalSubmitting}
        destroyOnHidden
      >
        <Form form={editStrategyForm} layout="vertical" onFinish={(values) => void handleUpdateStrategy(values)}>
          <Form.Item label="策略名" name="name" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item label="预算上限" name="limit" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={1000} step={1000} />
          </Form.Item>
          <Form.Item label="黄色阈值" name="yellowThreshold" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={0.5} max={2} step={0.05} />
          </Form.Item>
          <Form.Item label="红色阈值" name="redThreshold" rules={[{ required: true }]}>
            <InputNumber className="w-full" min={0.5} max={2} step={0.05} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
