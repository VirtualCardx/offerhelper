import { Button, Card, Input, Space, Table, message } from 'antd'
import { useEffect, useState } from 'react'

import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'
import type { TaskScheduleResponse, TaskStatusResponse } from '@/types/api'

export function TaskConsole() {
  const { demoContext, lastTaskId, setLastTaskId } = useAppStore()
  const [taskId, setTaskId] = useState(lastTaskId ?? '')
  const [schedules, setSchedules] = useState<TaskScheduleResponse[]>([])
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null)
  const [messageApi, contextHolder] = message.useMessage()

  useEffect(() => {
    void api.getTaskSchedules().then(setSchedules).catch(() => undefined)
  }, [])

  async function queryTaskStatus() {
    if (!taskId) return
    try {
      const result = await api.getTaskStatus(taskId)
      setTaskStatus(result)
      setLastTaskId(result.taskId)
    } catch (error) {
      messageApi.error(error instanceof Error ? error.message : '查询任务状态失败。')
    }
  }

  async function dispatchAlertScan() {
    const result = await api.dispatchAlertScan({
      modelName: 'baseline-offer-acceptance',
      operator: demoContext.operator,
      limit: 20,
    })
    setTaskId(result.taskId)
    setLastTaskId(result.taskId)
    messageApi.success(`已触发告警扫描任务：${result.taskId}`)
  }

  async function dispatchNotify() {
    const result = await api.dispatchNotifyTask({
      modelName: 'baseline-offer-acceptance',
      operator: demoContext.operator,
      channel: 'webhook-payload',
      destination: 'https://notify.example.local/governance',
      limit: 20,
    })
    setTaskId(result.taskId)
    setLastTaskId(result.taskId)
    messageApi.success(`已触发治理通知任务：${result.taskId}`)
  }

  return (
    <>
      {contextHolder}
      <div className="grid gap-4 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="glass-card" styles={{ body: { padding: 24 } }}>
          <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">计划任务</div>
          <Table
            rowKey="task"
            pagination={false}
            dataSource={schedules}
            columns={[
              { title: '任务', dataIndex: 'task', key: 'task' },
              { title: 'Cron', dataIndex: 'cron', key: 'cron' },
            ]}
          />
        </Card>

        <Card className="glass-card" styles={{ body: { padding: 24 } }}>
          <div className="mb-4 text-xs tracking-[0.22em] text-zinc-500 uppercase">任务控制台</div>
          <Space wrap>
            <Button onClick={() => void dispatchAlertScan()}>触发告警扫描</Button>
            <Button type="primary" onClick={() => void dispatchNotify()}>
              触发治理通知
            </Button>
          </Space>
          <div className="mt-5 flex gap-3">
            <Input value={taskId} onChange={(event) => setTaskId(event.target.value)} placeholder="输入或粘贴 taskId" />
            <Button onClick={() => void queryTaskStatus()}>查询状态</Button>
          </div>
          {taskStatus ? (
            <pre className="mt-4 overflow-auto rounded-2xl bg-black/40 p-4 text-xs text-zinc-300">
              {JSON.stringify(taskStatus, null, 2)}
            </pre>
          ) : null}
        </Card>
      </div>
    </>
  )
}
