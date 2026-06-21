import { useState } from 'react'

import { MetricCard } from '@/components/common/MetricCard'
import { AppShell } from '@/components/layout/AppShell'
import { CandidateWorkspaceForm } from '@/components/workspace/CandidateWorkspaceForm'
import { RecommendationPanel } from '@/components/workspace/RecommendationPanel'
import { formatCurrency, formatPercent } from '@/lib/format'
import type {
  CandidateResponse,
  MarketSalaryResponse,
  OfferRecommendationResponse,
  WorkspaceRecommendationTraceability,
} from '@/types/api'

export default function WorkspacePage() {
  const [candidate, setCandidate] = useState<CandidateResponse | null>(null)
  const [market, setMarket] = useState<MarketSalaryResponse | null>(null)
  const [offer, setOffer] = useState<OfferRecommendationResponse | null>(null)
  const [traceability, setTraceability] = useState<WorkspaceRecommendationTraceability | null>(null)

  return (
    <AppShell
      title="Offer 工作台"
      subtitle="把候选人输入、市场基准、预算约束和模型概率整合成一条可解释的薪酬推荐链路。"
    >
      <div className="mb-6 grid gap-4 xl:grid-cols-4">
        <MetricCard label="当前候选人" value={candidate?.name ?? '--'} hint={candidate?.level ? `级别 ${candidate.level}` : '等待创建候选人'} accent="zinc" />
        <MetricCard label="市场 P50" value={formatCurrency(market?.P50)} hint={market?.city ?? '等待市场数据'} accent="cyan" />
        <MetricCard label="推荐 Offer" value={formatCurrency(offer?.recommendedOffer)} hint={offer ? `竞争力 ${offer.competitivenessScore}` : '等待生成'} accent="amber" />
        <MetricCard label="接受概率" value={formatPercent(offer?.acceptProbability)} hint={offer?.riskLevel ? `风险 ${offer.riskLevel}` : '等待生成'} accent="rose" />
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.92fr_1.08fr]">
        <CandidateWorkspaceForm
          onCompleted={({ candidate: nextCandidate, market: nextMarket, offer: nextOffer, traceability: nextTraceability }) => {
            setCandidate(nextCandidate)
            setMarket(nextMarket)
            setOffer(nextOffer)
            setTraceability(nextTraceability)
          }}
        />
        <RecommendationPanel market={market} offer={offer} traceability={traceability} />
      </div>
    </AppShell>
  )
}
