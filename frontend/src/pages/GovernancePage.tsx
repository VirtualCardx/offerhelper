import { AppShell } from '@/components/layout/AppShell'
import { GovernanceOverview } from '@/components/governance/GovernanceOverview'

export default function GovernancePage() {
  return (
    <AppShell
      title="模型治理中心"
      subtitle="将训练记录、治理事件、待审批回滚、治理告警和通知预览汇聚到一个审计友好的控制平面。"
    >
      <GovernanceOverview />
    </AppShell>
  )
}
