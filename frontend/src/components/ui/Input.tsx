import { Search } from 'lucide-react'
import type {
  InputHTMLAttributes,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'

interface FieldWrapperProps {
  label?: string
  htmlFor?: string
  hint?: string
  error?: string | null
  children: React.ReactNode
}

function FieldWrapper({ label, htmlFor, hint, error, children }: FieldWrapperProps) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={htmlFor} className="text-xs font-medium text-zinc-300">
          {label}
        </label>
      )}
      {children}
      {error ? (
        <p className="text-xs text-red-400" role="alert">
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-zinc-500">{hint}</p>
      ) : null}
    </div>
  )
}

const baseFieldClass =
  'w-full rounded-lg border border-ip-border bg-ip-bg px-3 py-2 text-[13px] text-zinc-100 placeholder-zinc-500 transition-colors focus:border-ip-accent focus:outline-none disabled:opacity-50'

interface TextInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  hint?: string
  error?: string | null
}

export function TextInput({ label, hint, error, id, className = '', ...rest }: TextInputProps) {
  return (
    <FieldWrapper label={label} htmlFor={id} hint={hint} error={error}>
      <input
        id={id}
        className={`${baseFieldClass} ${error ? 'border-red-500/60 focus:border-red-400' : ''} ${className}`}
        {...rest}
      />
    </FieldWrapper>
  )
}

interface SearchInputProps extends InputHTMLAttributes<HTMLInputElement> {
  value: string
  onChangeValue: (val: string) => void
}

export function SearchInput({
  value,
  onChangeValue,
  placeholder = 'Search...',
  className = '',
  ...rest
}: SearchInputProps) {
  return (
    <div className={`relative ${className}`}>
      <Search
        size={15}
        className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-zinc-500"
        aria-hidden="true"
      />
      <input
        type="search"
        value={value}
        onChange={(e) => onChangeValue(e.target.value)}
        placeholder={placeholder}
        className={`${baseFieldClass} pl-9`}
        {...rest}
      />
    </div>
  )
}

interface TextareaInputProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  hint?: string
  error?: string | null
}

export function TextareaInput({
  label,
  hint,
  error,
  id,
  className = '',
  ...rest
}: TextareaInputProps) {
  return (
    <FieldWrapper label={label} htmlFor={id} hint={hint} error={error}>
      <textarea
        id={id}
        className={`${baseFieldClass} ${error ? 'border-red-500/60 focus:border-red-400' : ''} ${className}`}
        {...rest}
      />
    </FieldWrapper>
  )
}

interface SelectInputProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  hint?: string
  error?: string | null
}

export function SelectInput({
  label,
  hint,
  error,
  id,
  children,
  className = '',
  ...rest
}: SelectInputProps) {
  return (
    <FieldWrapper label={label} htmlFor={id} hint={hint} error={error}>
      <select id={id} className={`${baseFieldClass} ${className}`} {...rest}>
        {children}
      </select>
    </FieldWrapper>
  )
}
