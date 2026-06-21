import { BellRing, BriefcaseBusiness, ClipboardList, DatabaseZap, Radar, ShieldCheck } from 'lucide-react'
import { NavLink } from 'react-router-dom'

type AppShellProps = {
  title: string
  subtitle: string
  children: React.ReactNode
}

const navigationItems = [
  { to: '/workspace', label: 'Offer 工作台', icon: BriefcaseBusiness },
  { to: '/data-hub', label: '数据维护中心', icon: DatabaseZap },
  { to: '/offers', label: '候选人与 Offer', icon: ClipboardList },
  { to: '/governance', label: '模型治理中心', icon: ShieldCheck },
  { to: '/tasks', label: '任务与调度', icon: Radar },
]

export function AppShell({ title, subtitle, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.18),_transparent_24%),radial-gradient(circle_at_top_right,_rgba(244,63,94,0.14),_transparent_20%),linear-gradient(180deg,_rgba(255,255,255,0.02),_transparent_20%)]" />
      <div className="relative grid min-h-screen grid-cols-[260px_1fr]">
        <aside className="border-r border-white/10 bg-black/30 px-5 py-6 backdrop-blur-xl">
          <div className="mb-10">
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-cyan-400/30 bg-cyan-400/10 px-3 py-1 text-xs tracking-[0.25em] text-cyan-200 uppercase">
              <BellRing className="h-3.5 w-3.5" />
              AI Offer Console
            </div>
            <h1 className="font-serif text-3xl leading-tight text-white">企业薪酬决策驾驶舱</h1>
            <p className="mt-3 text-sm leading-6 text-zinc-400">
              将候选人、市场、薪酬策略、模型治理和审批动作汇聚到同一条决策链上。
            </p>
          </div>

          <nav className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    [
                      'group flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition-all',
                      isActive
                        ? 'border-cyan-400/40 bg-cyan-400/10 text-white shadow-[0_0_30px_rgba(34,211,238,0.12)]'
                        : 'border-white/5 bg-white/[0.03] text-zinc-400 hover:border-white/10 hover:bg-white/[0.05] hover:text-zinc-100',
                    ].join(' ')
                  }
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              )
            })}
          </nav>

          <div className="mt-10 rounded-3xl border border-white/10 bg-white/[0.04] p-4">
            <div className="text-xs tracking-[0.22em] text-zinc-500 uppercase">界面方向</div>
            <div className="mt-3 font-serif text-xl text-white">Graphite Control</div>
            <p className="mt-2 text-sm leading-6 text-zinc-400">
              深色石墨质感、冷白信息层、青蓝与洋红强调，突出风险、审批与模型状态。
            </p>
          </div>
        </aside>

        <main className="px-8 py-8">
          <header className="mb-8 flex items-end justify-between gap-8">
            <div>
              <div className="mb-2 text-xs tracking-[0.3em] text-zinc-500 uppercase">Decision Cockpit</div>
              <h2 className="font-serif text-4xl text-white">{title}</h2>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-zinc-400">{subtitle}</p>
            </div>
          </header>

          {children}
        </main>
      </div>
    </div>
  )
}
