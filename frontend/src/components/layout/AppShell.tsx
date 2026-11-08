import { Activity, FolderLock, Lock, QrCode, ShieldCheck, Smartphone } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'

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
            to="/login"
            className="group flex items-center gap-3 rounded-xl"
            aria-label="IPGuard home"
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

          {/* Navigation Links */}
          <nav className="flex items-center gap-2">
            <NavLink
              to="/login"
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? 'border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <QrCode size={14} />
              <span className="hidden sm:inline">QR Auth</span>
            </NavLink>

            <NavLink
              to="/devices"
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? 'border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Smartphone size={14} />
              <span className="hidden sm:inline">Devices</span>
            </NavLink>

            <NavLink
              to="/notes"
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? 'border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Lock size={14} />
              <span className="hidden sm:inline">Secure Notes</span>
            </NavLink>

            <NavLink
              to="/assets"
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? 'border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <FolderLock size={14} />
              <span className="hidden sm:inline">Asset Vault</span>
            </NavLink>

            <NavLink
              to="/system-status"
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? 'border border-ip-teal-400/30 bg-ip-teal-400/10 text-ip-teal-300 shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                }`
              }
            >
              <Activity size={14} />
              <span className="hidden sm:inline">System Status</span>
            </NavLink>
          </nav>

          <div className="flex items-center gap-3">
            <span className="rounded-full border border-ip-gold-400/20 bg-ip-gold-400/[0.06] px-3 py-1.5 text-[9px] font-semibold uppercase tracking-[0.2em] text-ip-gold-300">
              Auth & M3 Vault
            </span>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto w-full max-w-6xl flex-1 px-5 py-8 sm:px-8">
        <Outlet />
      </main>

      <footer className="relative z-10 border-t border-white/[0.06] bg-ip-navy-950/40 py-4 text-center text-[10px] text-slate-500 backdrop-blur-md">
        IPGuard • Hardware-Bound Cryptographic Digital Asset Security
      </footer>
    </div>
  )
}
