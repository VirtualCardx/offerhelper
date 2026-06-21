import { AppShell } from '@/components/layout/AppShell'
import { TaskConsole } from '@/components/tasks/TaskConsole'

export default function TasksPage() {
  return (
    <AppShell
      title="任务与调度"
      subtitle="查看治理巡检计划任务、触发告警扫描与通知任务，并按 taskId 追踪 Celery 执行结果。"
    >
      <TaskConsole />
    </AppShell>
  )
}
