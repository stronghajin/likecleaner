import { useEffect, useRef } from 'react'

const GLOW_SIZE = 180
// How quickly the glow catches up to the cursor each frame (0–1). Lower = softer trail.
const FOLLOW_SPEED = 0.18

// Soft white light that follows the mouse across every screen.
// It never blocks clicks and is turned off for users who prefer reduced motion.
export default function CursorGlow() {
  const glowRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const glow = glowRef.current
    if (!glow) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const target = { x: -GLOW_SIZE, y: -GLOW_SIZE }
    const current = { ...target }
    let frame = 0

    const render = () => {
      current.x += (target.x - current.x) * FOLLOW_SPEED
      current.y += (target.y - current.y) * FOLLOW_SPEED
      glow.style.transform = `translate3d(${current.x - GLOW_SIZE / 2}px, ${current.y - GLOW_SIZE / 2}px, 0)`
      const settled = Math.abs(target.x - current.x) < 0.5 && Math.abs(target.y - current.y) < 0.5
      frame = settled ? 0 : requestAnimationFrame(render)
    }

    const onMove = (e: MouseEvent) => {
      if (target.x < 0) {
        current.x = e.clientX
        current.y = e.clientY
      }
      target.x = e.clientX
      target.y = e.clientY
      glow.style.opacity = '1'
      if (!frame) frame = requestAnimationFrame(render)
    }
    const onLeave = () => {
      glow.style.opacity = '0'
    }

    window.addEventListener('mousemove', onMove)
    document.documentElement.addEventListener('mouseleave', onLeave)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('mousemove', onMove)
      document.documentElement.removeEventListener('mouseleave', onLeave)
    }
  }, [])

  return (
    <div
      ref={glowRef}
      aria-hidden
      className="pointer-events-none fixed top-0 left-0 z-50 rounded-full opacity-0 transition-opacity duration-300"
      style={{
        width: GLOW_SIZE,
        height: GLOW_SIZE,
        background:
          'radial-gradient(circle, color-mix(in srgb, var(--color-accent) 7%, transparent) 0%, transparent 65%)',
      }}
    />
  )
}
