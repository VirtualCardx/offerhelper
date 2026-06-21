import ReactECharts from 'echarts-for-react'
import { Alert, Card, Empty, Tag } from 'antd'

import { formatCurrency, formatDateTime, formatPercent } from '@/lib/format'
import type { MarketSalaryResponse, OfferRecommendationResponse, WorkspaceRecommendationTraceability } from '@/types/api'

type RecommendationPanelProps = {
  market: MarketSalaryResponse | null
  offer: OfferRecommendationResponse | null
  traceability: WorkspaceRecommendationTraceability | null
}

const selectedPointLabels = {
  min: '保守 min',
  target: '平衡 target',
  max: '激进 max',
} as const

export function RecommendationPanel({ market, offer, traceability }: RecommendationPanelProps) {
  if (!offer) {
    return (
      <div className="rounded-[28px] border border-white/10 bg-white/[0.04] p-6">
        <Empty
          description={<span className="text-zinc-400">提交候选人表单后，这里会展示推荐 Offer、风险与公平性解释。</span>}
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </div>
    )
  }

  const effectiveMarket = traceability?.market ?? market
  const selectedPointLabel = traceability ? selectedPointLabels[traceability.selectedPoint] : '--'
  const marketSnapshotId = effectiveMarket?.id ? `${effectiveMarket.id.slice(0, 8)}...` : '--'
  const strategySnapshotId = traceability?.strategy?.id ? `${traceability.strategy.id.slice(0, 8)}...` : offer.strategyId.slice(0, 8) + '...'
  const organizationSummary = [traceability?.company?.name, traceability?.department?.name].filter(Boolean).join(' / ') || '--'
  const businessSummary = [traceability?.company?.industry, traceability?.department?.domain].filter(Boolean).join(' / ') || '--'

  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-[1.25fr_0.95fr]">
        <Card className="glass-card" styles={{ body: { padding: 24 } }}>
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <div className="text-xs tracking-[0.22em] text-zinc-500 uppercase">推荐结果</div>
              <div className="mt-3 font-serif text-5xl text-white">{formatCurrency(offer.recommendedOffer)}</div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Tag color={offer.riskLevel === 'RED' ? 'red' : offer.riskLevel === 'YELLOW' ? 'gold' : 'cyan'}>
                  风险 {offer.riskLevel}
                </Tag>
                <Tag color="blue">模型 {offer.acceptanceModelVersion}</Tag>
                <Tag color="purple">CR {offer.crValue}</Tag>
              </div>
            </div>
            <div className="w-full max-w-[300px]">
              <ReactECharts
                style={{ height: 220 }}
                option={{
                  backgroundColor: 'transparent',
                  series: [
                    {
                      type: 'gauge',
                      startAngle: 220,
                      endAngle: -40,
                      radius: '88%',
                      progress: { show: true, width: 18, roundCap: true },
                      axisLine: { lineStyle: { width: 18, color: [[1, '#27272a']] } },
                      pointer: { show: false },
                      axisTick: { show: false },
                      splitLine: { show: false },
                      axisLabel: { show: false },
                      detail: {
                        valueAnimation: false,
                        color: '#f4f4f5',
                        fontSize: 28,
                        offsetCenter: [0, '10%'],
                        formatter: `${offer.competitivenessScore}`,
                      },
                      title: {
                        offsetCenter: [0, '42%'],
                        color: '#71717a',
                        fontSize: 12,
                      },
                      data: [{ value: offer.competitivenessScore, name: '竞争力评分' }],
                      max: 100,
                    },
                  ],
                }}
              />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
              <div className="text-xs tracking-[0.18em] text-zinc-500 uppercase">建议区间</div>
              <div className="mt-2 text-lg text-zinc-100">
                {formatCurrency(offer.range.min)} - {formatCurrency(offer.range.max)}
              </div>
            </div>
            <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
              <div className="text-xs tracking-[0.18em] text-zinc-500 uppercase">接受概率</div>
              <div className="mt-2 text-lg text-zinc-100">{formatPercent(offer.acceptProbability)}</div>
            </div>
            <div className="rounded-2xl border border-white/8 bg-black/20 p-4">
              <div className="text-xs tracking-[0.18em] text-zinc-500 uppercase">预算使用率</div>
              <div className="mt-2 text-lg text-zinc-100">{formatPercent(offer.budget.usageRatio)}</div>
            </div>
          </div>
        </Card>

        <Card className="glass-card" styles={{ body: { padding: 24 } }}>
          <div className="text-xs tracking-[0.22em] text-zinc-500 uppercase">市场参考</div>
          <div className="mt-4 space-y-3">
            <div className="rounded-2xl border border-white/8 bg-black/20 p-4 text-zinc-200">
              P25: {formatCurrency(effectiveMarket?.P25)}
            </div>
            <div className="rounded-2xl border border-cyan-300/20 bg-cyan-400/10 p-4 text-white">
              P50: {formatCurrency(effectiveMarket?.P50)}
            </div>
            <div className="rounded-2xl border border-white/8 bg-black/20 p-4 text-zinc-200">
              P75: {formatCurrency(effectiveMarket?.P75)}
            </div>
          </div>

          <Alert
            className="mt-5"
            message={`公平性评分 ${offer.equity.equityScore}`}
            description={offer.equity.message}
            type={offer.equity.riskLevel === 'HIGH' ? 'warning' : 'success'}
            showIcon
          />
        </Card>
      </div>

      <Card className="glass-card" styles={{ body: { padding: 24 } }}>
        <div className="text-xs tracking-[0.22em] text-zinc-500 uppercase">本次推荐依据</div>
        <div className="mt-4 grid gap-4 xl:grid-cols-2">
          <div className="rounded-2xl border border-white/8 bg-black/20 p-4 text-sm text-zinc-200">
            <div className="text-xs tracking-[0.18em] text-zinc-500 uppercase">策略快照</div>
            <div className="mt-3 text-base text-white">{traceability?.strategy?.name ?? '--'}</div>
            <div className="mt-2">组织范围 {organizationSummary}</div>
            <div className="mt-2">业务摘要 {businessSummary}</div>
            <div className="mt-2">策略 ID {strategySnapshotId}</div>
            <div className="mt-2">推荐锚点 {selectedPointLabel}</div>
            <div className="mt-2">预算上限 {formatCurrency(traceability?.strategy?.budgetPolicy.limit)}</div>
            <div className="mt-2">
              风险阈值 {traceability?.strategy?.budgetPolicy.yellowThreshold ?? '--'} /{' '}
              {traceability?.strategy?.budgetPolicy.redThreshold ?? '--'}
            </div>
            <div className="mt-2">CR 因子 {traceability?.strategy?.factors.length ?? 0} 个</div>
          </div>
          <div className="rounded-2xl border border-white/8 bg-black/20 p-4 text-sm text-zinc-200">
            <div className="text-xs tracking-[0.18em] text-zinc-500 uppercase">市场快照</div>
            <div className="mt-3 text-base text-white">{effectiveMarket?.city ?? '--'}</div>
            <div className="mt-2">快照 ID {marketSnapshotId}</div>
            <div className="mt-2">岗位 {traceability?.position?.title ?? '--'}</div>
            <div className="mt-2">报告来源 {effectiveMarket?.source ?? '--'}</div>
            <div className="mt-2">更新时间 {formatDateTime(effectiveMarket?.updateTime)}</div>
            <div className="mt-2">P50 {formatCurrency(effectiveMarket?.P50)}</div>
          </div>
        </div>
        <div className="mt-4 rounded-2xl border border-cyan-300/15 bg-cyan-400/10 p-4 text-sm text-zinc-100">
          本次推荐基于 {organizationSummary} 下的 {traceability?.position?.title ?? '--'} 在 {effectiveMarket?.city ?? '--'} 的市场快照，
          并按策略 {traceability?.strategy?.name ?? '--'} 的 {selectedPointLabel} 锚点生成。
        </div>
      </Card>

      <Card className="glass-card" styles={{ body: { padding: 24 } }}>
        <div className="text-xs tracking-[0.22em] text-zinc-500 uppercase">风险解释</div>
        <div className="mt-4 flex flex-wrap gap-3">
          {offer.riskReasons.map((reason) => (
            <div key={reason} className="rounded-full border border-white/10 bg-white/[0.04] px-4 py-2 text-sm text-zinc-300">
              {reason}
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
