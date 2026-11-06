import { ShieldCheck } from 'lucide-react'
import { Link, Outlet } from 'react-router-dom'

export function AppShell() {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden">
      <div
        className="pointer-events-none fixed inset-0 bg-grid opacity-50"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none fixed -left-40 top-24 size-96 rounded-full bg-ip-teal-500/[0.07] blur-3xl"
        aria-hidden="true"
      />
      <div
        className="pointer-events-none fixed -right-24 top-0 size-80 rounded-full bg-ip-gold-500/[0.05] blur-3xl"
        aria-hidden="true"
      />

      <header className="relative z-20 border-b border-white/[0.06] bg-ip-navy-950/55 backdrop-blur-xl">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-5 py-4 sm:px-8">
          <Link
            to="/system-status"
            className="group flex items-center gap-3 rounded-xl"
            aria-label="IPGuard system status home"
          >
            <span className="relative grid size-10 place-items-center rounded-2xl border border-ip-teal-400/25 bg-ip-teal-400/[0.08] text-ip-teal-300 shadow-[0_0_32px_-10px_rgba(45,212,191,0.6)] transition group-hover:border-ip-teal-300/40">
              <ShieldCheck
                size={22}
                strokeWidth={1.8}
                aria-hidden="true"
              />
              <span
                className="absolute -right-1 -top-1 size-2 rounded-full border border-ip-navy-950 bg-ip-gold-400"
                aria-hidden="true"
              />
            </span>
            <span>
              <span className="block font-display text-sm font-bold tracking-[0.24em] text-white">
                IPGUARD
              </span>
              <span className="block text-[9px] font-medium uppercase tracking-[0.2em] text-slate-500">
                Digital asset security
              </span>
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 text-xs font-medium text-slate-400 sm:flex">
              <span className="size-1.5 rounded-full bg-ip-teal-400" aria-hidden="true" />
              System status
            </span>
            <span className="rounded-full border border-ip-gold-400/20 bg-ip-gold-400/[0.06] px-3 py-1.5 text-[9px] font-semibold uppercase tracking-[0.2em] text-ip-gold-300">
              Foundation / M1
            </span>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-6xl flex-1 px-5 pb-16 pt-8 sm:px-8 sm:pt-12">
        <Outlet />
      </main>

      <footer className="relative z-10 border-t border-white/[0.05]">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-5 py-5 text-[10px] uppercase tracking-[0.16em] text-slate-600 sm:flex-row sm:items-center sm:justify-between sm:px-8">
          <span>IPGuard secure digital asset protection</span>
          <span>Readiness console · M0 + M1</span>
        </div>
      </footer>
    </div>
  )
}
