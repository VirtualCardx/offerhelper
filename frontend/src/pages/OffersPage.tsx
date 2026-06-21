import { AppShell } from '@/components/layout/AppShell'
import { OffersBoard } from '@/components/offers/OffersBoard'

export default function OffersPage() {
  return (
    <AppShell
      title="候选人与 Offer"
      subtitle="围绕最近生成的 Offer 展开查询、结果回写和报告生成，帮助 HR 将策略建议闭环到招聘结果。"
    >
      <OffersBoard />
    </AppShell>
  )
}
