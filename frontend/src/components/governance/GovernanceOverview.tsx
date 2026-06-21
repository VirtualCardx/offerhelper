import { Alert, Button, Card, Input, Select, Space, Table, message } from 'antd'
import { useEffect, useState } from 'react'

import { api } from '@/lib/api'
import { formatDateTime } from '@/lib/format'
import { useAppStore } from '@/store/useAppStore'
import type {
  GovernanceAlertResponse,
  GovernanceEventResponse,
  GovernanceNotificationResponse,
  ModelVersionResponse,
  TrainingRunResponse,
} from '@/types/api'

export function GovernanceOverview() {
  const { demoContext } = useAppStore()
  const [activeModel, setActiveModel] = useState<ModelVersionResponse | null>(null)
  const [trainingRuns, setTrainingRuns] = useState<TrainingRunResponse[]>([])
  const [events, setEvents] = useState<GovernanceEventResponse[]>([])
  const [alerts, setAlerts] = useState<GovernanceAlertResponse[]>([])
  const [selectedEventId, setSelectedEventId] = useState<string>('')
  const [approvalTicket, setApprovalTicket] = useState('APR-3001')
  const [notification, setNotification] = useState<GovernanceNotificationResponse | null>(null)
  const [messageApi, contextHolder] = message.useMessage()

  async function refresh() {
    try {
      const [model, runs, governanceEvents, governanceAlerts] = await Promise.all([
        api.getActiveModel('baseline-offer-acceptance'),
        api.listTrainingRuns('baseline-offer-acceptance'),
        api.listGovernanceEvents({ modelName: 'baseline-offer-acceptance', limit: 20 }),
        api.listGovernanceAlerts({ modelName: 'baseline-offer-acceptance', operator: demoContext.operator, limit: 20 }),
      ])
      setActiveModel(model)
      setTrainingRuns(runs)
      setEvents(governanceEvents)
      setAlerts(governanceAlerts)
      const pending = governanceEvents.find((item) => item.status === 'PENDING')
      setSelectedEventId(pending?.id ?? '')
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '加载治理中心数据失败。')
    }
  }

  async function approvePending() {
    if (!selectedEventId) return
    await api.reviewGovernanceEvent(selectedEventId, {
      action: 'APPROVE',
      reviewer: demoContext.reviewer,
      comment: '前端治理中心审批通过。',
      approvalTicket,
    })
    messageApi.success('待审批回滚已处理。')
    await refresh()
  }

  async function previewNotification() {
    const result = await api.notifyGovernanceAlerts({
      modelName: 'baseline-offer-acceptance',
      operator: demoContext.operator,
      channel: 'log',
      limit: 10,
    })
    setNotification(result)
  }

  useEffect(() => {
    void refresh()
  }, [demoContext.operator])

  return (
    <>
      {contextHolder}
      <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-4">
          <Card className="glass-card" styles={{ body: { padding: 24 } }}>
            <div className="text-xs tracking-[0.22em] text-zinc-500 uppercase">活动模型</div>
            <div className="mt-3 font-serif text-3xl text-white">{activeModel?.modelVersion ?? '--'}</div>
            <div className="mt-2 text-sm text-zinc-400">
              {activeModel?.framework ?? '--'} / {activeModel?.status ?? '--'}
            </div>
          </Card>

          <Card className="glass-card" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">待审批操作台</div>
            <Space direction="vertical" className="w-full">
              <Select
                value={selectedEventId || undefined}
                placeholder="选择待审批事件"
                onChange={setSelectedEventId}
                options={events.filter((item) => item.status === 'PENDING').map((item) => ({ value: item.id, label: item.id }))}
              />
              <Input value={approvalTicket} onChange={(event) => setApprovalTicket(event.target.value)} />
              <Button type="primary" onClick={() => void approvePending()} disabled={!selectedEventId}>
                审批通过
              </Button>
            </Space>
          </Card>

          <Card className="glass-card" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">通知预览</div>
            <Button onClick={() => void previewNotification()}>生成通知预览</Button>
            {notification ? (
              <pre className="mt-4 overflow-auto rounded-2xl bg-black/40 p-4 text-xs text-zinc-300">
                {JSON.stringify(notification.deliveries, null, 2)}
              </pre>
            ) : null}
          </Card>
        </div>

        <div className="space-y-4">
          <Card className="glass-card" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">治理告警</div>
            <div className="space-y-3">
              {alerts.map((alert) => (
                <Alert
                  key={alert.id}
                  type={alert.severity === 'CRITICAL' ? 'error' : alert.severity === 'HIGH' ? 'warning' : 'info'}
                  message={`${alert.alertType} / ${alert.status}`}
                  description={alert.message}
                  showIcon
                />
              ))}
            </div>
          </Card>

          <Card className="glass-card" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">训练记录</div>
            <Table
              rowKey="id"
              size="small"
              pagination={{ pageSize: 4 }}
              dataSource={trainingRuns}
              columns={[
                { title: '版本', dataIndex: 'modelVersion', key: 'modelVersion' },
                { title: '来源', dataIndex: 'source', key: 'source' },
                { title: '准确率', dataIndex: 'trainingAccuracy', key: 'trainingAccuracy' },
                { title: '激活', dataIndex: 'activated', key: 'activated', render: (value: boolean) => (value ? '是' : '否') },
              ]}
            />
          </Card>

          <Card className="glass-card" styles={{ body: { padding: 24 } }}>
            <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">治理事件时间线</div>
            <div className="space-y-3">
              {events.map((event) => (
                <div key={event.id} className="rounded-2xl border border-white/8 bg-black/20 p-4 text-sm text-zinc-300">
                  <div className="flex items-center justify-between gap-3">
                    <span>{event.eventType}</span>
                    <span>{event.status}</span>
                  </div>
                  <div className="mt-1 text-zinc-500">{event.operator} / {formatDateTime(event.createdAt)}</div>
                  <div className="mt-2">{event.reason}</div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </>
  )
}
