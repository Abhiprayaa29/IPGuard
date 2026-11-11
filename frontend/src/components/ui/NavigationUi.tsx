import { ChevronLeft, ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

export interface TabOption<T extends string> {
  id: T
  label: string
  count?: number
}

interface TabsProps<T extends string> {
  options: TabOption<T>[]
  activeId: T
  onChange: (id: T) => void
  className?: string
}

export function Tabs<T extends string>({
  options,
  activeId,
  onChange,
  className = '',
}: TabsProps<T>) {
  return (
    <div
      role="tablist"
      className={`inline-flex flex-wrap items-center gap-1 rounded-lg border border-ip-border bg-ip-bg p-1 ${className}`}
    >
      {options.map((tab) => {
        const active = tab.id === activeId
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onChange(tab.id)}
            className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors cursor-pointer ${
              active
                ? 'bg-ip-elevated text-zinc-100 border border-ip-border-strong'
                : 'text-zinc-400 hover:text-zinc-200 border border-transparent'
            }`}
          >
            <span>{tab.label}</span>
            {typeof tab.count === 'number' && (
              <span className="tabular-nums text-[11px] text-zinc-500">{tab.count}</span>
            )}
          </button>
        )
      })}
    </div>
  )
}

export interface BreadcrumbItem {
  label: string
  to?: string
}

export function Breadcrumb({ items }: { items: BreadcrumbItem[] }) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-zinc-500">
      {items.map((item, idx) => (
        <span key={item.label} className="inline-flex items-center gap-1.5">
          {idx > 0 && <ChevronRight size={12} aria-hidden="true" />}
          {item.to ? (
            <Link to={item.to} className="hover:text-zinc-200 transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="text-zinc-300 font-medium">{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}

interface PaginationProps {
  page: number
  totalPages: number
  onPageChange: (nextPage: number) => void
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null
  return (
    <div className="flex items-center justify-between border-t border-ip-border px-4 py-3 text-xs text-zinc-400">
      <span className="tabular-nums">
        Page {page} of {totalPages}
      </span>
      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Previous page"
          className="inline-flex h-7 items-center gap-1 rounded border border-ip-border bg-ip-elevated px-2.5 text-zinc-300 hover:bg-ip-hover disabled:opacity-40"
        >
          <ChevronLeft size={13} />
          Prev
        </button>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          aria-label="Next page"
          className="inline-flex h-7 items-center gap-1 rounded border border-ip-border bg-ip-elevated px-2.5 text-zinc-300 hover:bg-ip-hover disabled:opacity-40"
        >
          Next
          <ChevronRight size={13} />
        </button>
      </div>
    </div>
  )
}

export function Tooltip({ text, children }: { text: string; children: ReactNode }) {
  return (
    <span title={text} className="inline-flex items-center">
      {children}
    </span>
  )
}
