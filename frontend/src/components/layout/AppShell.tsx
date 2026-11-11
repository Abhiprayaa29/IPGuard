import {
  Activity,
  FileText,
  FolderLock,
  LayoutDashboard,
  LogOut,
  Menu,
  QrCode,
  ScanEye,
  ShieldCheck,
  Smartphone,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { clearStoredSessionToken, getStoredSessionToken } from '../../utils/session'

interface NavItem {
  to: string
  label: string
  icon: typeof LayoutDashboard
}

const navItems: NavItem[] = [
  { to: '/overview', label: 'Overview', icon: LayoutDashboard },
  { to: '/login', label: 'QR Authentication', icon: QrCode },
  { to: '/devices', label: 'Devices', icon: Smartphone },
  { to: '/notes', label: 'Secure Notes', icon: FileText },
  { to: '/assets', label: 'Asset Vault', icon: FolderLock },
  { to: '/steganography', label: 'Steganography Lab', icon: ScanEye },
  { to: '/system-status', label: 'System Status', icon: Activity },
]

export function AppShell() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [hasSession, setHasSession] = useState<boolean>(() => Boolean(getStoredSessionToken()))
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    setHasSession(Boolean(getStoredSessionToken()))
    setMobileMenuOpen(false)
  }, [location.pathname, location.key])

  useEffect(() => {
    if (!mobileMenuOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileMenuOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [mobileMenuOpen])

  const handleSignOut = () => {
    clearStoredSessionToken()
    setHasSession(false)
    navigate('/login')
  }

  const renderNavLinks = () => (
    <nav aria-label="Primary navigation" className="flex flex-col gap-1">
      {navItems.map((item) => {
        const Icon = item.icon
        return (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-2.5 rounded-lg px-3 py-2 text-[13px] font-medium transition-colors ${
                isActive
                  ? 'bg-ip-elevated text-zinc-100 border border-ip-border-strong'
                  : 'text-zinc-400 hover:bg-ip-elevated/60 hover:text-zinc-100 border border-transparent'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon
                  size={15}
                  className={isActive ? 'text-ip-accent-hover' : 'text-zinc-500'}
                  aria-hidden="true"
                />
                <span>{item.label}</span>
              </>
            )}
          </NavLink>
        )
      })}
    </nav>
  )

  return (
    <div className="flex min-h-screen bg-ip-bg text-zinc-100">
      {/* Compact Desktop Sidebar */}
      <aside className="hidden lg:flex lg:w-60 lg:flex-col lg:border-r lg:border-ip-border lg:bg-ip-surface lg:shrink-0">
        <div className="flex h-14 items-center gap-2.5 border-b border-ip-border px-4">
          <Link to="/overview" className="flex items-center gap-2.5" aria-label="IPGuard home">
            <span className="flex size-7 items-center justify-center rounded-md border border-ip-accent/35 bg-ip-accent/10 text-ip-accent-hover">
              <ShieldCheck size={16} aria-hidden="true" />
            </span>
            <span className="text-sm font-semibold tracking-tight text-zinc-100">IPGuard</span>
          </Link>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4">{renderNavLinks()}</div>

        <div className="border-t border-ip-border p-3">
          <div className="rounded-lg border border-ip-border bg-ip-bg px-3 py-2.5">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-medium text-zinc-300">
                {hasSession ? 'Session active' : 'No active session'}
              </span>
              <span
                className={`size-2 rounded-full ${
                  hasSession ? 'bg-emerald-400' : 'bg-zinc-600'
                }`}
                aria-hidden="true"
              />
            </div>
            <p className="mt-0.5 text-[11px] text-zinc-500">
              {hasSession
                ? 'Hardware bearer session stored in browser.'
                : 'Sign in with QR to unlock vaults.'}
            </p>
            <div className="mt-2.5">
              {hasSession ? (
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-ip-border bg-ip-elevated px-2.5 py-1.5 text-xs font-medium text-zinc-300 hover:bg-ip-hover hover:text-zinc-100"
                >
                  <LogOut size={12} aria-hidden="true" />
                  Sign Out
                </button>
              ) : (
                <Link
                  to="/login"
                  className="inline-flex w-full items-center justify-center gap-1.5 rounded-md border border-ip-accent/40 bg-ip-accent/10 px-2.5 py-1.5 text-xs font-medium text-ip-accent-hover hover:bg-ip-accent/20"
                >
                  <QrCode size={12} aria-hidden="true" />
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Shell */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile & Tablet Top Bar */}
        <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-ip-border bg-ip-surface/95 px-4 backdrop-blur lg:hidden">
          <Link to="/overview" className="flex items-center gap-2">
            <span className="flex size-7 items-center justify-center rounded-md border border-ip-accent/35 bg-ip-accent/10 text-ip-accent-hover">
              <ShieldCheck size={15} aria-hidden="true" />
            </span>
            <span className="text-sm font-semibold text-zinc-100">IPGuard</span>
          </Link>

          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-medium ${
                hasSession
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                  : 'border-ip-border bg-ip-elevated text-zinc-400'
              }`}
            >
              <span
                className={`size-1.5 rounded-full ${hasSession ? 'bg-emerald-400' : 'bg-zinc-500'}`}
                aria-hidden="true"
              />
              {hasSession ? 'Signed in' : 'Locked'}
            </span>
            <button
              type="button"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open navigation menu"
              className="inline-flex size-9 items-center justify-center rounded-lg border border-ip-border bg-ip-elevated text-zinc-200 hover:bg-ip-hover"
            >
              <Menu size={17} />
            </button>
          </div>
        </header>

        {/* Mobile Drawer */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 z-50 flex lg:hidden"
            role="dialog"
            aria-modal="true"
            aria-label="Mobile navigation"
          >
            <div
              className="fixed inset-0 bg-black/70"
              onClick={() => setMobileMenuOpen(false)}
              aria-hidden="true"
            />
            <div className="relative z-10 flex w-72 max-w-[85vw] flex-col border-r border-ip-border bg-ip-surface p-4">
              <div className="mb-4 flex items-center justify-between border-b border-ip-border pb-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck size={16} className="text-ip-accent-hover" />
                  <span className="text-sm font-semibold text-zinc-100">IPGuard Navigation</span>
                </div>
                <button
                  type="button"
                  onClick={() => setMobileMenuOpen(false)}
                  aria-label="Close navigation menu"
                  className="rounded-md p-1 text-zinc-400 hover:bg-ip-elevated hover:text-zinc-100"
                >
                  <X size={16} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto">{renderNavLinks()}</div>
              <div className="mt-4 border-t border-ip-border pt-3">
                {hasSession ? (
                  <button
                    type="button"
                    onClick={handleSignOut}
                    className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-ip-border bg-ip-elevated px-3 py-2 text-xs font-medium text-zinc-200"
                  >
                    <LogOut size={13} />
                    Sign Out
                  </button>
                ) : (
                  <Link
                    to="/login"
                    className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-ip-accent bg-ip-accent px-3 py-2 text-xs font-semibold text-zinc-950"
                  >
                    <QrCode size={13} />
                    Sign In with QR
                  </Link>
                )}
              </div>
            </div>
          </div>
        )}

        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
