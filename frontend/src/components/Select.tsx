import type { SelectHTMLAttributes } from 'react'

export default function Select({ className = '', ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={`h-9 rounded-sm border bg-panel px-3 text-text outline-none hover:border-muted focus:border-muted ${className}`}
      {...rest}
    />
  )
}
