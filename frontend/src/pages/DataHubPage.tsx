import { AppShell } from '@/components/layout/AppShell'
import { DataHubConsole } from '@/components/data-hub/DataHubConsole'

export default function DataHubPage() {
  return (
    <AppShell
      title="数据维护中心"
      subtitle="集中维护市场薪资、内部员工薪资和薪酬策略，让 Offer 推荐与公平性分析始终基于最新业务输入。"
    >
      <DataHubConsole />
    </AppShell>
  )
}
