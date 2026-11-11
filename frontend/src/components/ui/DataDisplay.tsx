import type { ReactNode } from 'react'

import { Breadcrumb, type BreadcrumbItem } from './NavigationUi'

interface PageHeaderProps {
  title: string
  description: string
  breadcrumbs?: BreadcrumbItem[]
  actions?: ReactNode
}

export function PageHeader({ title, description, breadcrumbs, actions }: PageHeaderProps) {
  return (
    <header className="flex flex-col gap-4 border-b border-ip-border pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="space-y-1">
        {breadcrumbs && breadcrumbs.length > 0 && <Breadcrumb items={breadcrumbs} />}
        <h1 className="text-xl font-semibold tracking-tight text-zinc-100 sm:text-2xl">
          {title}
        </h1>
        <p className="max-w-2xl text-[13px] text-zinc-400">{description}</p>
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2 shrink-0">{actions}</div>}
    </header>
  )
}

interface PanelProps {
  title?: string
  description?: string
  actions?: ReactNode
  noPadding?: boolean
  className?: string
  children: ReactNode
}

export function Panel({
  title,
  description,
  actions,
  noPadding = false,
  className = '',
  children,
}: PanelProps) {
  return (
    <section
      className={`rounded-xl border border-ip-border bg-ip-surface ${className}`}
    >
      {(title || description || actions) && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ip-border px-5 py-3.5">
          <div>
            {title && <h2 className="text-sm font-semibold text-zinc-100">{title}</h2>}
            {description && <p className="mt-0.5 text-xs text-zinc-400">{description}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div className={noPadding ? '' : 'p-5'}>{children}</div>
    </section>
  )
}

export interface KeyValueItem {
  label: string
  value: ReactNode
  mono?: boolean
}

export function KeyValueGrid({
  items,
  columns = 2,
}: {
  items: KeyValueItem[]
  columns?: 2 | 3
}) {
  const colClass = columns === 3 ? 'sm:grid-cols-2 lg:grid-cols-3' : 'sm:grid-cols-2'
  return (
    <dl className={`grid grid-cols-1 gap-x-6 gap-y-4 ${colClass}`}>
      {items.map((item) => (
        <div key={item.label} className="min-w-0">
          <dt className="text-xs text-zinc-500">{item.label}</dt>
          <dd
            className={`mt-1 text-[13px] text-zinc-100 break-words ${
              item.mono ? 'font-mono text-xs' : 'font-medium'
            }`}
          >
            {item.value}
          </dd>
        </div>
      ))}
    </dl>
  )
}
