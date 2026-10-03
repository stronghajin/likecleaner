import { useEffect } from 'react'
import type { ReactNode } from 'react'

interface ModalProps {
  title: string
  onClose: () => void
  children: ReactNode
  /** Buttons row at the bottom. */
  footer?: ReactNode
  width?: number
}

// Centered dialog. Escape or a click on the dark backdrop closes it.
export default function Modal({ title, onClose, children, footer, width = 520 }: ModalProps) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-bg/80 animate-[fade-in_150ms_ease-out]"
      onPointerDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        style={{ width }}
        className="max-h-[85vh] overflow-y-auto border bg-panel shadow-2xl shadow-bg animate-[dialog-in_180ms_ease-out]"
      >
        <h2 className="border-b px-6 py-4 text-base font-semibold">{title}</h2>
        <div className="px-6 py-5">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t px-6 py-4">{footer}</div>}
      </div>
    </div>
  )
}
