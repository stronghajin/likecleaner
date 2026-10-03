import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'secondary' | 'danger' | 'ghost'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-accent text-bg hover:bg-accent/85',
  secondary: 'border text-text hover:border-muted hover:bg-text/5',
  // Final button of destructive actions (SPEC.md section 11).
  danger: 'bg-danger text-text hover:bg-danger/85',
  ghost: 'text-muted hover:bg-text/5 hover:text-text',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
}

export default function Button({ variant = 'secondary', className = '', ...rest }: ButtonProps) {
  return (
    <button
      type="button"
      className={`inline-flex items-center justify-center gap-2 rounded-sm px-4 py-2 font-medium disabled:cursor-not-allowed disabled:opacity-40 ${VARIANTS[variant]} ${className}`}
      {...rest}
    />
  )
}
