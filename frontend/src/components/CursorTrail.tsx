import { useEffect, useRef } from 'react'
import { ICON_SHAPES } from './icons'

// The tail, front to back: like, subscribe bell, play, add to playlist.
const ICONS = [ICON_SHAPES.like, ICON_SHAPES.bell, ICON_SHAPES.play, ICON_SHAPES.playlist]

const ICON_SIZE = 16
// Each icon chases the one in front of it; lower = longer, lazier tail.
const FOLLOW_SPEED = 0.12
// Where the tail starts, measured from the cursor tip (down-right, clear of the arrow).
const OFFSET = { x: 22, y: 24 }
// How fast the tail fades out after the mouse stops (per frame).
const FADE_SPEED = 0.94

// A short tail of outline icons that follows the mouse and fades away when it stops.
export default function CursorTrail() {
  const iconRefs = useRef<(SVGSVGElement | null)[]>([])

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const cursor = { x: 0, y: 0 }
    const points = ICONS.map(() => ({ x: 0, y: 0 }))
    let started = false
    let activity = 0
    let frame = 0

    const render = () => {
      points.forEach((p, i) => {
        const leader = i === 0 ? cursor : points[i - 1]
        p.x += (leader.x - p.x) * FOLLOW_SPEED
        p.y += (leader.y - p.y) * FOLLOW_SPEED
        const icon = iconRefs.current[i]
        if (!icon) return
        const scale = 1 - i * 0.12
        icon.style.transform = `translate3d(${p.x - ICON_SIZE / 2}px, ${p.y - ICON_SIZE / 2}px, 0) scale(${scale})`
        icon.style.opacity = String(activity * (0.8 - i * 0.15))
      })
      activity *= FADE_SPEED
      frame = activity > 0.01 ? requestAnimationFrame(render) : 0
    }

    const onMove = (e: MouseEvent) => {
      cursor.x = e.clientX + OFFSET.x
      cursor.y = e.clientY + OFFSET.y
      if (!started) {
        points.forEach((p) => Object.assign(p, cursor))
        started = true
      }
      activity = 1
      if (!frame) frame = requestAnimationFrame(render)
    }

    window.addEventListener('mousemove', onMove)
    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('mousemove', onMove)
    }
  }, [])

  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 z-50">
      {ICONS.map((icon, i) => (
        <svg
          key={i}
          ref={(el) => {
            iconRefs.current[i] = el
          }}
          className="absolute top-0 left-0 opacity-0"
          width={ICON_SIZE}
          height={ICON_SIZE}
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth={1.75}
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {icon}
        </svg>
      ))}
    </div>
  )
}
